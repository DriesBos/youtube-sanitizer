from pathlib import Path
from typing import List

from .db import connect, get_auth_snapshot, iter_feed_rows, set_watched_state
from .models import AuthStatusResponse, FeedItem


def list_feed_items(database_path: Path, limit: int) -> List[FeedItem]:
    normalised_limit = max(1, min(limit, 200))

    with connect(database_path) as connection:
        rows = iter_feed_rows(connection, normalised_limit).fetchall()

    return [
        FeedItem(
            videoId=row["video_id"],
            title=row["title"],
            channelName=row["channel_name"],
            publishedAt=row["published_at"],
            description=row["description"],
            duration=row["duration"],
            thumbnailUrl=row["thumbnail_url"],
            isWatched=bool(row["is_watched"]),
        )
        for row in rows
    ]


def mark_video_watched(database_path: Path, video_id: str) -> bool:
    with connect(database_path) as connection:
        return set_watched_state(connection, video_id, True)


def get_auth_status(database_path: Path, configured: bool) -> AuthStatusResponse:
    with connect(database_path) as connection:
        snapshot = get_auth_snapshot(connection)

    return AuthStatusResponse(
        configured=configured,
        connected=snapshot.connected,
        lastSyncAt=snapshot.last_sync_at,
        subscriptionCount=snapshot.subscription_count,
        videoCount=snapshot.video_count,
    )
