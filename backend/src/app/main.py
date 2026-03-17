from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import load_settings
from .db import initialize_database
from .feed_store import list_feed_items, mark_video_watched
from .models import FeedResponse, WatchStateResponse


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
