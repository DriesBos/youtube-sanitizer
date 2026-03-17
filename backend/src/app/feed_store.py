from pathlib import Path
from typing import List

from .db import connect, iter_feed_rows
from .models import FeedItem


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
