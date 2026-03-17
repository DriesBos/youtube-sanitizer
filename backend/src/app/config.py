from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def _resolve_database_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path

    backend_root = Path(__file__).resolve().parents[2]
    return backend_root / path


@dataclass(frozen=True)
class Settings:
    app_env: str
    app_host: str
    app_port: int
    app_base_url: str
    frontend_base_url: str
    frontend_base_urls: tuple[str, ...]
    database_path: Path
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str
    youtube_api_scope: str
    sync_recent_per_channel: int


def load_settings() -> Settings:
    frontend_base_url = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")
    frontend_base_urls_raw = os.getenv("FRONTEND_BASE_URLS", frontend_base_url)
    frontend_base_urls = tuple(
        value.strip() for value in frontend_base_urls_raw.split(",") if value.strip()
    )
    app_base_url = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")
    google_redirect_uri = os.getenv(
        "GOOGLE_REDIRECT_URI", f"{app_base_url}/api/auth/google/callback"
    )

    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        app_host=os.getenv("APP_HOST", "127.0.0.1"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        app_base_url=app_base_url,
        frontend_base_url=frontend_base_url,
        frontend_base_urls=frontend_base_urls or (frontend_base_url,),
        database_path=_resolve_database_path(
            os.getenv("DATABASE_PATH", "./data/youtube_sanitizer.db")
        ),
        google_client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
        google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
        google_redirect_uri=google_redirect_uri,
        youtube_api_scope=os.getenv(
            "YOUTUBE_API_SCOPE",
            "https://www.googleapis.com/auth/youtube.readonly",
        ),
        sync_recent_per_channel=max(1, int(os.getenv("SYNC_RECENT_PER_CHANNEL", "3"))),
    )
