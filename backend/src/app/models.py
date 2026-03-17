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
