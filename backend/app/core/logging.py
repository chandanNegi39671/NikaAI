"""
backend/app/core/logging.py
────────────────────────────
Structured logging configuration for the Nika AI backend.

Produces machine-readable JSON logs in production (consumable by log
aggregators like Datadog, CloudWatch, or Loki) and human-readable coloured
text output in development for easy readability.

Architecture:
  - Wraps Python stdlib `logging` — no third-party log library dependency.
  - A single root logger is configured once at application startup via
    `setup_logging()`.
  - Child loggers are obtained via `get_logger(__name__)` in each module.
  - Every log record includes a `request_id` field when available (injected
    by middleware in future sprints).

Usage:
    from app.core.logging import get_logger
    logger = get_logger(__name__)
    logger.info("Model loaded", extra={"model_path": str(path)})
"""

from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# JSON Formatter
# ─────────────────────────────────────────────────────────────────────────────

class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects.

    Emitted fields:
        timestamp   ISO-8601 UTC timestamp
        level       Log level name (INFO, WARNING, ERROR, …)
        logger      Logger name (usually the module's __name__)
        message     The log message
        **extra     Any extra key=value pairs passed via `extra={}`
    """

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        # Build the base payload
        payload: dict[str, Any] = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Attach exception traceback if present
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        # Attach any extra fields the caller passed via extra={}
        # Standard LogRecord attributes are excluded to avoid noise.
        _STDLIB_KEYS = frozenset(logging.LogRecord(
            "", 0, "", 0, "", (), None
        ).__dict__.keys()) | {"message", "asctime"}

        for key, value in record.__dict__.items():
            if key not in _STDLIB_KEYS:
                payload[key] = value

        return json.dumps(payload, default=str, ensure_ascii=False)


# ─────────────────────────────────────────────────────────────────────────────
# Text Formatter (development)
# ─────────────────────────────────────────────────────────────────────────────

_TEXT_FORMAT = (
    "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
)
_DATE_FORMAT = "%H:%M:%S"


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def setup_logging(level: str = "INFO", fmt: str = "json") -> None:
    """Configure the root logger for the application.

    Call once at application startup (inside ``main.py`` lifespan handler).

    Args:
        level: Logging level string. One of DEBUG, INFO, WARNING, ERROR.
        fmt:   Output format. ``"json"`` for production, ``"text"`` for dev.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    handlers = []
    
    # 1. Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    handlers.append(console_handler)
    
    # 2. Rotating File Handler
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        filename=log_dir / "nika_ai.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    handlers.append(file_handler)

    if fmt == "json":
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(fmt=_TEXT_FORMAT, datefmt=_DATE_FORMAT)

    for h in handlers:
        h.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(numeric_level)

    # Remove any pre-existing handlers (e.g. added by uvicorn)
    root.handlers.clear()
    for h in handlers:
        root.addHandler(h)

    # Silence overly verbose third-party loggers
    for noisy in ("ultralytics", "urllib3", "httpx", "PIL"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named child logger.

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        A standard :class:`logging.Logger` instance.
    """
    return logging.getLogger(name)
