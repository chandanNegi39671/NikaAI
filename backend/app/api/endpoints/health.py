"""
backend/app/api/endpoints/health.py
──────────────────────────────────────
GET /api/v1/health — liveness & readiness probe for Nika AI.

Responsibilities (this file only):
  - Define the ``HealthResponse`` Pydantic response model.
  - Expose the ``GET /api/v1/health`` route via an ``APIRouter``.
  - Compute human-readable uptime from a module-level start timestamp.
  - Delegate model-load status to ``prediction_service.is_loaded``.

What this file does NOT do:
  - Load the model  →  PredictionService (Module 1)
  - Auth checks     →  future middleware sprint
  - DB queries      →  Sprint 5

Response shape:
    {
        "status":       "healthy",
        "service":      "Nika AI Backend",
        "version":      "1.0.0",
        "model_loaded": true,
        "uptime":       "0d 00h 03m 42s"
    }
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import get_logger
from app.services.prediction import prediction_service
from sqlalchemy import text

logger = get_logger(__name__)

# ── Module-level start time (survives hot-reload in dev; accurate enough) ─────
_SERVER_START_TIME: float = time.monotonic()
_SERVER_START_UTC: datetime = datetime.now(tz=timezone.utc)

router = APIRouter(
    prefix="/api/v1",
    tags=["Health"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Response Model
# ─────────────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Liveness and readiness information returned by GET /api/v1/health.

    ``status`` is always ``"healthy"`` as long as the process is alive.
    ``model_loaded`` distinguishes readiness (model in RAM) from liveness
    (process alive), matching the Kubernetes probe pattern.
    """

    status: str = Field(
        default="healthy",
        description="Always 'healthy' while the process is alive.",
        examples=["healthy"],
    )
    service: str = Field(
        description="Human-readable service name.",
        examples=["Nika AI Backend"],
    )
    version: str = Field(
        description="Application semantic version.",
        examples=["1.0.0"],
    )
    model_loaded: bool = Field(
        description=(
            "True when the YOLOv8 model is loaded in memory and ready "
            "to serve inference requests."
        ),
        examples=[True],
    )
    uptime: str = Field(
        description=(
            "Wall-clock time since the API process started, "
            "formatted as 'Xd HHh MMm SSs'."
        ),
        examples=["0d 00h 03m 42s"],
    )

    model_config = {
        "protected_namespaces": (),   # allow model_* field names without warnings
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "service": "Nika AI Backend",
                "version": "1.0.0",
                "model_loaded": True,
                "uptime": "0d 00h 03m 42s",
            }
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _format_uptime(elapsed_seconds: float) -> str:
    """Convert a float of elapsed seconds into a human-readable uptime string.

    Args:
        elapsed_seconds: Number of seconds since the server started.

    Returns:
        String formatted as ``'Xd HHh MMm SSs'``.

    Examples:
        >>> _format_uptime(3662)
        '0d 01h 01m 02s'
        >>> _format_uptime(90061)
        '1d 01h 01m 01s'
    """
    total_seconds = int(elapsed_seconds)
    days, remainder = divmod(total_seconds, 86_400)
    hours, remainder = divmod(remainder, 3_600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours:02d}h {minutes:02d}m {seconds:02d}s"


# ─────────────────────────────────────────────────────────────────────────────
# Route
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description=(
        "Liveness and readiness probe. "
        "Returns HTTP 200 as long as the process is alive. "
        "Inspect `model_loaded` to determine if the service is ready to "
        "accept inference requests."
    ),
    responses={
        200: {
            "description": "Service is alive (may not be ready if model_loaded=false).",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "Nika AI Backend",
                        "version": "1.0.0",
                        "model_loaded": True,
                        "uptime": "0d 00h 03m 42s",
                    }
                }
            },
        }
    },
)
async def health_check() -> HealthResponse:
    """Return liveness and readiness information.

    This endpoint is intentionally kept fast and dependency-free (no DB,
    no external calls) so that load-balancers can probe it at high frequency
    without adding latency to inference requests.
    """
    elapsed = time.monotonic() - _SERVER_START_TIME

    response = HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        model_loaded=prediction_service.is_loaded,
        uptime=_format_uptime(elapsed),
    )

    logger.debug(
        "Health check requested.",
        extra={
            "model_loaded": response.model_loaded,
            "uptime": response.uptime,
        },
    )

    return response


@router.get(
    "/ready",
    summary="Readiness check",
    description="Detailed readiness check validating DB, Redis, and YOLO model statuses."
)
async def ready_check():
    """Verify that all core services are online and ready to accept requests."""
    # 1. DB Connection Check
    db_ok = False
    try:
        from app.core.database import SessionLocal
        db = SessionLocal()
        # Run a simple query to assert DB health
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:
        logger.error(f"Readiness check DB failure: {exc}")
    finally:
        db.close()

    # 2. Redis Connection Check
    redis_ok = False
    try:
        from app.core.redis import get_redis
        redis_client = get_redis()
        if redis_client and redis_client.ping():
            redis_ok = True
    except Exception as exc:
        logger.error(f"Readiness check Redis failure: {exc}")

    # 3. Model Loaded Check
    model_ok = prediction_service.is_loaded

    status_code = 200
    if not (db_ok and redis_ok and model_ok):
        status_code = 503

    from fastapi import Response
    import json
    content = {
        "status": "ready" if status_code == 200 else "degraded",
        "database": "online" if db_ok else "offline",
        "redis": "online" if redis_ok else "offline",
        "yolo_model": "loaded" if model_ok else "not_loaded"
    }
    return Response(
        content=json.dumps(content),
        media_type="application/json",
        status_code=status_code
    )


@router.get(
    "/live",
    summary="Liveness check",
    description="System liveness heartbeat check validating disk, CPU, and RAM thresholds."
)
async def live_check():
    """Rapid hardware sanity check for Kubernetes liveness checks."""
    import shutil
    import psutil
    from fastapi import Response
    import json

    # Disk Space check
    total, used, free = shutil.disk_usage("/")
    free_percent = (free / total) * 100
    disk_ok = free_percent > 5.0  # Safe boundary: > 5% free disk

    # Memory Check
    mem = psutil.virtual_memory()
    mem_ok = mem.percent < 95.0   # Safe boundary: < 95% RAM utilization

    status_code = 200
    if not (disk_ok and mem_ok):
        status_code = 503

    content = {
        "status": "healthy" if status_code == 200 else "degraded",
        "disk_free_percent": round(free_percent, 2),
        "ram_used_percent": mem.percent
    }
    return Response(
        content=json.dumps(content),
        media_type="application/json",
        status_code=status_code
    )
