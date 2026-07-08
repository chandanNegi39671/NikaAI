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

import os
import secrets
from enum import Enum
from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


# ── Resolve the repository root so paths are stable regardless of CWD ────────
_BACKEND_ROOT: Path = Path(__file__).resolve().parents[2]

def _get_secret(name: str, default: str) -> str:
    """Load secret from Docker/K8s secret file, fallback to environment."""
    import os
    secret_path = Path(f"/run/secrets/{name}")
    if secret_path.exists():
        try:
            return secret_path.read_text().strip()
        except Exception:
            pass
    return os.getenv(name.upper(), default)


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
    database_url: str = _get_secret("database_url", "sqlite:///./nika.db")
    redis_url: str = _get_secret("redis_url", "redis://localhost:6379/0")
    celery_broker_url: str = _get_secret("celery_broker_url", "redis://localhost:6379/1")
    celery_result_backend: str = _get_secret("celery_result_backend", "redis://localhost:6379/2")

    # ── JWT Authentication ────────────────────────────────────────────────────
    # No hardcoded fallback: a fixed default baked into source becomes public
    # the moment the repo is shared, letting anyone forge valid JWTs. In
    # production this must come from the environment / secrets file. In
    # development we generate a random per-process key so local runs still
    # work without ever writing a real default into source control.
    secret_key: str = _get_secret("secret_key", secrets.token_hex(32))
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7


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

    # ── Sprint 8: AI Provider Selection ───────────────────────────────────────
    # Controls which LLM adapter the Copilot service uses at runtime.
    # Values: rule_based | ollama | gemma | openai | huggingface
    llm_provider: str = "rule_based"

    # Controls which knowledge retrieval backend is used.
    # Values: keyword | vector
    knowledge_provider: str = "keyword"

    # Optional: LLM endpoint URLs (used by non-rule-based adapters)
    ollama_base_url: str = "http://localhost:11434"
    gemma_api_url: str = ""
    openai_api_key: str = ""
    hf_api_key: str = ""

    # ── Notifications (Sprint 7) ───────────────────────────────────────────────
    # SMTP
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_address: str = "alerts@nika.ai"
    smtp_use_tls: bool = True

    # Webhook integrations
    slack_webhook_url: str = ""
    teams_webhook_url: str = ""
    discord_webhook_url: str = ""

    # Twilio SMS
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""

    # Dispatch behaviour
    notification_max_retries: int = 3
    notification_escalation_minutes: int = 15  # unacknowledged critical alerts escalate after this many minutes


    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @model_validator(mode="after")
    def enforce_secret_key_in_production(self) -> "Settings":
        """Fail fast rather than silently signing production tokens with a
        throwaway per-process key generated because SECRET_KEY was unset."""
        has_explicit_secret = (
            Path("/run/secrets/secret_key").exists() or bool(os.getenv("SECRET_KEY"))
        )
        if self.env == Environment.PRODUCTION and not has_explicit_secret:
            raise ValueError(
                "SECRET_KEY must be set explicitly (env var or /run/secrets/secret_key) "
                "when ENV=production. Refusing to start with a generated key."
            )
        return self

    @field_validator("confidence_threshold")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("CONFIDENCE_THRESHOLD must be between 0.0 and 1.0")
        return v


# ── Singleton instance ────────────────────────────────────────────────────────
settings: Settings = Settings()