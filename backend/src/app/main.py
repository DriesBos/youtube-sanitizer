from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Optional
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .config import load_settings
from .db import connect, consume_oauth_state, create_oauth_state, initialize_database, save_token
from .feed_store import get_auth_status, list_feed_items, mark_video_watched
from .google_oauth import (
    GoogleOAuthError,
    build_google_auth_url,
    build_token_values,
    exchange_code_for_token,
    is_google_configured,
)
from .models import AuthStatusResponse, FeedResponse, SyncResponse, WatchStateResponse
from .youtube_sync import YouTubeSyncError, sync_youtube_data


settings = load_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database(settings.database_path)
    yield


app = FastAPI(
    title="YouTube Sanitizer API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.frontend_base_urls),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict:
    return {
        "ok": True,
        "environment": settings.app_env,
    }


@app.get("/api/auth/status", response_model=AuthStatusResponse)
async def auth_status() -> AuthStatusResponse:
    return get_auth_status(settings.database_path, is_google_configured(settings))


@app.get("/api/auth/google/start")
async def google_auth_start():
    if not is_google_configured(settings):
        raise HTTPException(
            status_code=503, detail="Google OAuth credentials are not configured."
        )

    with connect(settings.database_path) as connection:
        state = create_oauth_state(connection)

    return RedirectResponse(build_google_auth_url(settings, state), status_code=302)


@app.get("/api/auth/google/callback")
async def google_auth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    if error:
        return RedirectResponse(
            f"{settings.frontend_base_url}?{urlencode({'auth': error})}", status_code=302
        )
    if not code or not state:
        return RedirectResponse(
            f"{settings.frontend_base_url}?{urlencode({'auth': 'missing_code'})}",
            status_code=302,
        )

    with connect(settings.database_path) as connection:
        valid_state = consume_oauth_state(connection, state)

    if not valid_state:
        return RedirectResponse(
            f"{settings.frontend_base_url}?{urlencode({'auth': 'invalid_state'})}",
            status_code=302,
        )

    try:
        token_payload = exchange_code_for_token(settings, code)
        access_token, refresh_token, scope, expires_at = build_token_values(token_payload)
        with connect(settings.database_path) as connection:
            save_token(connection, access_token, refresh_token, scope, expires_at)

        sync_youtube_data(settings)
        redirect_query = urlencode({"auth": "connected"})
    except (GoogleOAuthError, YouTubeSyncError) as error_message:
        redirect_query = urlencode({"auth": "error", "detail": str(error_message)[:120]})

    return RedirectResponse(f"{settings.frontend_base_url}?{redirect_query}", status_code=302)


@app.get("/api/feed", response_model=FeedResponse)
async def get_feed(limit: int = Query(default=60, ge=1, le=200)) -> FeedResponse:
    items = list_feed_items(settings.database_path, limit)
    return FeedResponse(items=items)


@app.post("/api/feed/{video_id}/watched", response_model=WatchStateResponse)
async def set_video_watched(video_id: str) -> WatchStateResponse:
    updated = mark_video_watched(settings.database_path, video_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Video not found")

    return WatchStateResponse(videoId=video_id, isWatched=True)


@app.post("/api/sync", response_model=SyncResponse)
async def sync_feed() -> SyncResponse:
    if not is_google_configured(settings):
        raise HTTPException(
            status_code=503, detail="Google OAuth credentials are not configured."
        )

    try:
        result = sync_youtube_data(settings)
    except (GoogleOAuthError, YouTubeSyncError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return SyncResponse(
        connected=result.connected,
        subscriptionCount=result.subscription_count,
        videoCount=result.video_count,
        syncedAt=result.synced_at,
    )
