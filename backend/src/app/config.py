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
    database_path: Path


def load_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        app_host=os.getenv("APP_HOST", "127.0.0.1"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        app_base_url=os.getenv("APP_BASE_URL", "http://127.0.0.1:8000"),
        frontend_base_url=os.getenv("FRONTEND_BASE_URL", "http://localhost:5173"),
        database_path=_resolve_database_path(
            os.getenv("DATABASE_PATH", "./data/youtube_sanitizer.db")
        ),
    )
