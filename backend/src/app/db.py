from pathlib import Path
import sqlite3
from typing import Iterator

from .models import FeedItem


SCHEMA = """
CREATE TABLE IF NOT EXISTS feed_items (
    video_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    channel_name TEXT NOT NULL,
    published_at TEXT NOT NULL,
    description TEXT,
    duration TEXT,
    thumbnail_url TEXT,
    is_watched INTEGER NOT NULL DEFAULT 0
);
"""


SEED_ITEMS = [
    FeedItem(
        videoId="dQw4w9WgXcQ",
        title="A surprisingly sharp breakdown of modern web performance",
        channelName="Frontend Field Notes",
        publishedAt="2026-03-17T13:10:00Z",
        description="A seed item that stands in for the eventual backend feed.",
        duration="18:24",
        isWatched=False,
    ),
    FeedItem(
        videoId="3JZ_D3ELwOQ",
        title="Weekly design systems review and release notes",
        channelName="Component Office",
        publishedAt="2026-03-17T11:40:00Z",
        description="Seed content keeps the page usable while the backend is still being built.",
        duration="26:41",
        isWatched=True,
    ),
    FeedItem(
        videoId="L_jWHffIx5E",
        title="Shipping a tiny app with fewer moving parts",
        channelName="Quiet Architecture",
        publishedAt="2026-03-16T19:05:00Z",
        description="Chronological ordering is applied server-side before the page renders.",
        duration="12:09",
        isWatched=False,
    ),
    FeedItem(
        videoId="Zi_XLOBDo_Y",
        title="The case for server-owned feeds and cached merges",
        channelName="Systems Weekly",
        publishedAt="2026-03-16T16:25:00Z",
        description="The UI accepts optional watched status from the backend when it exists.",
        duration="31:12",
        isWatched=False,
    ),
    FeedItem(
        videoId="fJ9rUzIMcZQ",
        title="What actually matters for a single-user media app",
        channelName="One Box Ops",
        publishedAt="2026-03-15T22:15:00Z",
        description="Local watched-state can bridge the gap until a richer backend exists.",
        duration="9:58",
        isWatched=True,
    ),
]


def ensure_parent_directory(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)


def connect(database_path: Path) -> sqlite3.Connection:
    ensure_parent_directory(database_path)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(database_path: Path) -> None:
    with connect(database_path) as connection:
        connection.execute(SCHEMA)
        row = connection.execute("SELECT COUNT(*) AS count FROM feed_items").fetchone()
        count = int(row["count"]) if row is not None else 0

        if count == 0:
            connection.executemany(
                """
                INSERT INTO feed_items (
                    video_id,
                    title,
                    channel_name,
                    published_at,
                    description,
                    duration,
                    thumbnail_url,
                    is_watched
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        item.video_id,
                        item.title,
                        item.channel_name,
                        item.published_at,
                        item.description,
                        item.duration,
                        item.thumbnail_url,
                        int(item.is_watched),
                    )
                    for item in SEED_ITEMS
                ],
            )
        connection.commit()


def iter_feed_rows(
    connection: sqlite3.Connection, limit: int
) -> Iterator[sqlite3.Row]:
    query = """
    SELECT
        video_id,
        title,
        channel_name,
        published_at,
        description,
        duration,
        thumbnail_url,
        is_watched
    FROM feed_items
    ORDER BY datetime(published_at) DESC
    LIMIT ?
    """
    return connection.execute(query, (limit,))


def set_watched_state(
    connection: sqlite3.Connection, video_id: str, is_watched: bool
) -> bool:
    cursor = connection.execute(
        """
        UPDATE feed_items
        SET is_watched = ?
        WHERE video_id = ?
        """,
        (int(is_watched), video_id),
    )
    connection.commit()
    return cursor.rowcount > 0
