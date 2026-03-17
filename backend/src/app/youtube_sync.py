from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

import httpx

from .config import Settings
from .db import (
    SubscriptionRow,
    connect,
    finish_sync_run,
    get_token,
    parse_iso,
    replace_feed_items,
    replace_subscriptions,
    save_token,
    start_sync_run,
    utc_now,
    utc_now_iso,
)
from .google_oauth import GoogleOAuthError, build_token_values, refresh_access_token
from .models import FeedItem


YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


@dataclass
class SyncResult:
    connected: bool
    subscription_count: int
    video_count: int
    synced_at: str | None


class YouTubeSyncError(RuntimeError):
    pass


def _chunked(values: list[str], size: int) -> Iterable[list[str]]:
    for index in range(0, len(values), size):
        yield values[index : index + size]


def _format_duration(value: str | None) -> str | None:
    if not value:
        return None

    match = re.fullmatch(
        r"P(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)",
        value,
    )
    if not match:
        return None

    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = int(match.group("seconds") or 0)

    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def _authorised_client(access_token: str) -> httpx.Client:
    return httpx.Client(
        base_url=YOUTUBE_API_BASE,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30.0,
    )


def _get_valid_access_token(settings: Settings) -> str:
    with connect(settings.database_path) as connection:
        token = get_token(connection)
        if token is None:
            raise YouTubeSyncError("No Google account is connected.")

        if parse_iso(token.expires_at).timestamp() - 60 > utc_now().timestamp():
            return token.access_token

    if not settings.google_client_id or not settings.google_client_secret:
        raise YouTubeSyncError("Google OAuth credentials are missing on the backend.")

    refreshed = refresh_access_token(settings, token)
    access_token, refresh_token, scope, expires_at = build_token_values(refreshed)

    with connect(settings.database_path) as connection:
        save_token(connection, access_token, refresh_token, scope, expires_at)

    return access_token


def _fetch_subscriptions(settings: Settings, client: httpx.Client) -> list[dict]:
    items: list[dict] = []
    page_token: str | None = None

    while True:
        params = {
            "part": "snippet,contentDetails",
            "mine": "true",
            "maxResults": 50,
        }
        if page_token:
            params["pageToken"] = page_token

        response = client.get("/subscriptions", params=params)
        if response.status_code >= 400:
            raise YouTubeSyncError(response.text)

        payload = response.json()
        items.extend(payload.get("items", []))
        page_token = payload.get("nextPageToken")
        if not page_token:
            break

    return items


def _fetch_channels(client: httpx.Client, channel_ids: list[str]) -> dict[str, dict]:
    result: dict[str, dict] = {}

    for chunk in _chunked(channel_ids, 50):
        response = client.get(
            "/channels",
            params={
                "part": "snippet,contentDetails",
                "id": ",".join(chunk),
                "maxResults": 50,
            },
        )
        if response.status_code >= 400:
            raise YouTubeSyncError(response.text)

        for item in response.json().get("items", []):
            result[item["id"]] = item

    return result


def _fetch_playlist_video_ids(
    client: httpx.Client, playlist_id: str, max_results: int
) -> list[str]:
    response = client.get(
        "/playlistItems",
        params={
            "part": "snippet,contentDetails",
            "playlistId": playlist_id,
            "maxResults": max_results,
        },
    )
    if response.status_code >= 400:
        raise YouTubeSyncError(response.text)

    items = response.json().get("items", [])
    video_ids: list[str] = []
    for item in items:
        content_details = item.get("contentDetails", {})
        snippet = item.get("snippet", {})
        resource = snippet.get("resourceId", {})
        video_id = content_details.get("videoId") or resource.get("videoId")
        if video_id:
            video_ids.append(video_id)
    return video_ids


def _fetch_video_details(client: httpx.Client, video_ids: list[str]) -> list[dict]:
    details: list[dict] = []

    for chunk in _chunked(video_ids, 50):
        response = client.get(
            "/videos",
            params={
                "part": "snippet,contentDetails",
                "id": ",".join(chunk),
                "maxResults": 50,
            },
        )
        if response.status_code >= 400:
            raise YouTubeSyncError(response.text)
        details.extend(response.json().get("items", []))

    return details


def _pick_thumbnail(snippet: dict) -> str | None:
    thumbnails = snippet.get("thumbnails", {})
    for key in ("maxres", "standard", "high", "medium", "default"):
        url = thumbnails.get(key, {}).get("url")
        if url:
            return url
    return None


def sync_youtube_data(settings: Settings) -> SyncResult:
    access_token = _get_valid_access_token(settings)

    with connect(settings.database_path) as connection:
        run_id = start_sync_run(connection)

    try:
        with _authorised_client(access_token) as client:
            subscription_items = _fetch_subscriptions(settings, client)
            channel_ids = [
                item.get("snippet", {})
                .get("resourceId", {})
                .get("channelId")
                for item in subscription_items
            ]
            channel_ids = [channel_id for channel_id in channel_ids if channel_id]

            channel_map = _fetch_channels(client, channel_ids)
            synced_at = utc_now_iso()

            subscriptions: list[SubscriptionRow] = []
            recent_video_ids: list[str] = []
            for channel_id in channel_ids:
                channel = channel_map.get(channel_id)
                if not channel:
                    continue

                snippet = channel.get("snippet", {})
                uploads_playlist_id = (
                    channel.get("contentDetails", {})
                    .get("relatedPlaylists", {})
                    .get("uploads")
                )
                if not uploads_playlist_id:
                    continue

                subscriptions.append(
                    SubscriptionRow(
                        channel_id=channel_id,
                        title=snippet.get("title", "Unknown channel"),
                        thumbnail_url=_pick_thumbnail(snippet),
                        uploads_playlist_id=uploads_playlist_id,
                        synced_at=synced_at,
                    )
                )
                recent_video_ids.extend(
                    _fetch_playlist_video_ids(
                        client,
                        uploads_playlist_id,
                        settings.sync_recent_per_channel,
                    )
                )

            unique_video_ids = list(dict.fromkeys(recent_video_ids))
            video_items = _fetch_video_details(client, unique_video_ids)
            feed_items = [
                FeedItem(
                    videoId=item["id"],
                    title=item.get("snippet", {}).get("title", "Untitled"),
                    channelName=item.get("snippet", {}).get("channelTitle", "Unknown channel"),
                    publishedAt=item.get("snippet", {}).get("publishedAt", synced_at),
                    description=item.get("snippet", {}).get("description"),
                    duration=_format_duration(
                        item.get("contentDetails", {}).get("duration")
                    ),
                    thumbnailUrl=_pick_thumbnail(item.get("snippet", {})),
                    isWatched=False,
                )
                for item in sorted(
                    video_items,
                    key=lambda current: current.get("snippet", {}).get("publishedAt", ""),
                    reverse=True,
                )
            ]

        with connect(settings.database_path) as connection:
            replace_subscriptions(connection, subscriptions)
            replace_feed_items(connection, feed_items)
            finish_sync_run(connection, run_id, "success")

        return SyncResult(
            connected=True,
            subscription_count=len(subscriptions),
            video_count=len(feed_items),
            synced_at=synced_at,
        )
    except (GoogleOAuthError, YouTubeSyncError, httpx.HTTPError) as error:
        with connect(settings.database_path) as connection:
            finish_sync_run(connection, run_id, "error", str(error))
        raise
