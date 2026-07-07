"""
backend/app/core/config.py
──────────────────────────
Centralised application settings loaded from environment variables
(or a .env file in development).

Uses pydantic-settings BaseSettings so every field is:
  - Type-validated by Pydantic
  - Overridable via environment variable or .env file
  - Documented in one place

Usage:
    from app.core.config import settings
    print(settings.model_path)
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


# ── Resolve the repository root so paths are stable regardless of CWD ────────
_BACKEND_ROOT: Path = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """All runtime configuration for the Nika AI backend."""

    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=(),   # allow model_* field names without warnings
    )

    # ── Application ───────────────────────────────────────────────────────────
    env: Environment = Environment.DEVELOPMENT
    app_name: str = "Nika AI"
    app_version: str = "0.1.0"
    debug: bool = False
    database_url: str = "sqlite:///./nika.db"


    # ── Server ────────────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # ── Model ─────────────────────────────────────────────────────────────────
    # Absolute path to the local YOLOv8 weights file.
    model_path: Path = _BACKEND_ROOT / "app" / "models" / "best.pt"

    # Inference settings
    confidence_threshold: float = 0.25
    warmup_image_size: tuple[int, int] = (640, 640)

    # ── Uploads ───────────────────────────────────────────────────────────────
    max_image_bytes: int = 10 * 1024 * 1024  # 10 MB
    min_image_dimension: int = 32            # pixels — both axes must meet this minimum
    allowed_image_formats: list[str] = ["image/jpeg", "image/png", "image/webp"]

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_format: str = "json"


# ── Singleton instance ────────────────────────────────────────────────────────
settings: Settings = Settings()
