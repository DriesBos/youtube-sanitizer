from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import load_settings
from .db import initialize_database
from .feed_store import list_feed_items
from .models import FeedResponse


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
    allow_origins=[settings.frontend_base_url],
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
