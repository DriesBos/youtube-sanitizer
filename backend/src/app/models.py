from typing import List, Optional

from pydantic import BaseModel, Field


class FeedItem(BaseModel):
    video_id: str = Field(alias="videoId")
    title: str
    channel_name: str = Field(alias="channelName")
    published_at: str = Field(alias="publishedAt")
    description: Optional[str] = None
    duration: Optional[str] = None
    thumbnail_url: Optional[str] = Field(default=None, alias="thumbnailUrl")
    is_watched: bool = Field(default=False, alias="isWatched")

    model_config = {
        "populate_by_name": True,
    }


class FeedResponse(BaseModel):
    items: List[FeedItem]


class WatchStateResponse(BaseModel):
    video_id: str = Field(alias="videoId")
    is_watched: bool = Field(alias="isWatched")

    model_config = {
        "populate_by_name": True,
    }


class AuthStatusResponse(BaseModel):
    configured: bool
    connected: bool
    redirect_uri: Optional[str] = Field(default=None, alias="redirectUri")
    last_sync_at: Optional[str] = Field(default=None, alias="lastSyncAt")
    subscription_count: int = Field(default=0, alias="subscriptionCount")
    video_count: int = Field(default=0, alias="videoCount")

    model_config = {
        "populate_by_name": True,
    }


class SyncResponse(BaseModel):
    connected: bool
    subscription_count: int = Field(alias="subscriptionCount")
    video_count: int = Field(alias="videoCount")
    synced_at: Optional[str] = Field(default=None, alias="syncedAt")

    model_config = {
        "populate_by_name": True,
    }
