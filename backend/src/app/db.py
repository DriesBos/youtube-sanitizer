from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import secrets
import sqlite3
from typing import Iterable, Iterator, Sequence

from .models import FeedItem


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@dataclass
class TokenRecord:
    access_token: str
    refresh_token: str
    scope: str
    expires_at: str


@dataclass
class AuthSnapshot:
    connected: bool
    last_sync_at: str | None
    subscription_count: int
    video_count: int


@dataclass
class SubscriptionRow:
    channel_id: str
    title: str
    thumbnail_url: str | None
    uploads_playlist_id: str
    synced_at: str


SCHEMA_STATEMENTS = [
    """
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
    """,
    """
    CREATE TABLE IF NOT EXISTS oauth_tokens (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        access_token TEXT NOT NULL,
        refresh_token TEXT NOT NULL,
        scope TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS oauth_states (
        state TEXT PRIMARY KEY,
        created_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriptions (
        channel_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        thumbnail_url TEXT,
        uploads_playlist_id TEXT NOT NULL,
        synced_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS sync_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        started_at TEXT NOT NULL,
        finished_at TEXT,
        status TEXT NOT NULL,
        detail TEXT
    );
    """,
]


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
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)

        row = connection.execute("SELECT COUNT(*) AS count FROM feed_items").fetchone()
        count = int(row["count"]) if row is not None else 0

        if count == 0:
            replace_feed_items(connection, SEED_ITEMS)

        connection.commit()


def iter_feed_rows(connection: sqlite3.Connection, limit: int) -> Iterator[sqlite3.Row]:
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


def set_watched_state(connection: sqlite3.Connection, video_id: str, is_watched: bool) -> bool:
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


def create_oauth_state(connection: sqlite3.Connection) -> str:
    cleanup_oauth_states(connection)
    state = secrets.token_urlsafe(32)
    connection.execute(
        "INSERT INTO oauth_states (state, created_at) VALUES (?, ?)",
        (state, utc_now_iso()),
    )
    connection.commit()
    return state


def consume_oauth_state(connection: sqlite3.Connection, state: str) -> bool:
    cleanup_oauth_states(connection)
    cursor = connection.execute("DELETE FROM oauth_states WHERE state = ?", (state,))
    connection.commit()
    return cursor.rowcount > 0


def cleanup_oauth_states(connection: sqlite3.Connection) -> None:
    threshold = (utc_now() - timedelta(minutes=20)).isoformat()
    connection.execute("DELETE FROM oauth_states WHERE created_at < ?", (threshold,))
    connection.commit()


def save_token(
    connection: sqlite3.Connection,
    access_token: str,
    refresh_token: str,
    scope: str,
    expires_at: str,
) -> None:
    connection.execute(
        """
        INSERT INTO oauth_tokens (id, access_token, refresh_token, scope, expires_at, updated_at)
        VALUES (1, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            access_token = excluded.access_token,
            refresh_token = excluded.refresh_token,
            scope = excluded.scope,
            expires_at = excluded.expires_at,
            updated_at = excluded.updated_at
        """,
        (access_token, refresh_token, scope, expires_at, utc_now_iso()),
    )
    connection.commit()


def get_token(connection: sqlite3.Connection) -> TokenRecord | None:
    row = connection.execute(
        """
        SELECT access_token, refresh_token, scope, expires_at
        FROM oauth_tokens
        WHERE id = 1
        """
    ).fetchone()
    if row is None:
        return None

    return TokenRecord(
        access_token=row["access_token"],
        refresh_token=row["refresh_token"],
        scope=row["scope"],
        expires_at=row["expires_at"],
    )


def replace_subscriptions(
    connection: sqlite3.Connection, subscriptions: Sequence[SubscriptionRow]
) -> None:
    connection.execute("DELETE FROM subscriptions")
    connection.executemany(
        """
        INSERT INTO subscriptions (
            channel_id,
            title,
            thumbnail_url,
            uploads_playlist_id,
            synced_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                item.channel_id,
                item.title,
                item.thumbnail_url,
                item.uploads_playlist_id,
                item.synced_at,
            )
            for item in subscriptions
        ],
    )
    connection.commit()


def replace_feed_items(connection: sqlite3.Connection, items: Sequence[FeedItem]) -> None:
    watched_rows = connection.execute(
        "SELECT video_id, is_watched FROM feed_items"
    ).fetchall()
    watched_map = {row["video_id"]: bool(row["is_watched"]) for row in watched_rows}

    connection.execute("DELETE FROM feed_items")
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
                int(watched_map.get(item.video_id, item.is_watched)),
            )
            for item in items
        ],
    )
    connection.commit()


def start_sync_run(connection: sqlite3.Connection) -> int:
    cursor = connection.execute(
        """
        INSERT INTO sync_runs (started_at, status)
        VALUES (?, ?)
        """,
        (utc_now_iso(), "running"),
    )
    connection.commit()
    return int(cursor.lastrowid)


def finish_sync_run(
    connection: sqlite3.Connection, run_id: int, status: str, detail: str | None = None
) -> None:
    connection.execute(
        """
        UPDATE sync_runs
        SET finished_at = ?, status = ?, detail = ?
        WHERE id = ?
        """,
        (utc_now_iso(), status, detail, run_id),
    )
    connection.commit()


def get_auth_snapshot(connection: sqlite3.Connection) -> AuthSnapshot:
    token = get_token(connection)
    last_sync_row = connection.execute(
        """
        SELECT finished_at
        FROM sync_runs
        WHERE status = 'success'
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()
    subscription_row = connection.execute(
        "SELECT COUNT(*) AS count FROM subscriptions"
    ).fetchone()
    video_row = connection.execute(
        "SELECT COUNT(*) AS count FROM feed_items"
    ).fetchone()

    return AuthSnapshot(
        connected=token is not None,
        last_sync_at=last_sync_row["finished_at"] if last_sync_row is not None else None,
        subscription_count=int(subscription_row["count"]) if subscription_row is not None else 0,
        video_count=int(video_row["count"]) if video_row is not None else 0,
    )
