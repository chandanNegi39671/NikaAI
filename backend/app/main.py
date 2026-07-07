"""
backend/app/main.py
────────────────────
FastAPI application factory for Nika AI.

Responsibilities:
  - Create and configure the FastAPI app instance.
  - Register the lifespan handler (startup / shutdown hooks).
  - Configure CORS middleware.
  - Mount the single versioned API router from ``app.api``.

The lifespan handler calls ``load_model()`` then ``warmup()`` once at
startup so the YOLOv8 model is compiled and resident in memory for all requests.

Sprint 1 routes (defined in their own endpoint modules):
  GET  /api/v1/health    — liveness + model status (app/api/endpoints/health.py)
  POST /api/v1/predict   — image upload → defect detections (app/api/endpoints/prediction.py)

Router assembly:
  main.py  →  app.api.router  →  health_router + prediction_router
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router                        # single versioned router — all routes
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.services.prediction import prediction_service

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Lifespan — startup & shutdown hooks
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle resources.

    Startup:
      1. Configure structured logging.
      2. Load the YOLOv8 model from disk (raises ModelNotFoundError if missing).
      3. Run one warmup forward pass to pre-compile the model graph.

    Shutdown:
      - Placeholder for future DB connection pool teardown (Sprint 5).
    """
    # ── Startup ───────────────────────────────────────────────────────────────
    setup_logging(level=settings.log_level, fmt=settings.log_format)

    logger.info(
        "Starting Nika AI backend.",
        extra={
            "app": settings.app_name,
            "version": settings.app_version,
            "env": settings.env.value,
        },
    )

    try:
        from app.core.db_init import init_db
        init_db()
    except Exception as exc:
        logger.error(
            "Failed to initialize database during startup.",
            extra={"error": str(exc), "type": type(exc).__name__},
        )

    try:
        prediction_service.load_model()
        prediction_service.warmup()
        logger.info(
            "PredictionService ready.",
            extra={
                "num_classes": len(prediction_service.class_names),
                "model_path": str(settings.model_path),
            },
        )
    except Exception as exc:
        # Log but do NOT crash the server — /health still responds so
        # operators can diagnose without SSH access.
        logger.error(
            "Failed to initialise PredictionService during startup.",
            extra={"error": str(exc), "type": type(exc).__name__},
        )

    yield  # Application is now running — requests are served here

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("Nika AI backend shutting down.")


# ─────────────────────────────────────────────────────────────────────────────
# Application Factory
# ─────────────────────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Build and configure the FastAPI application.

    Returns:
        A fully configured ``FastAPI`` instance ready to be served by uvicorn.
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "AI-powered manufacturing defect detection API. "
            "Upload an image to receive YOLOv8 defect detections with "
            "bounding boxes and confidence scores."
        ),
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routes ────────────────────────────────────────────────────────────────
    # The versioned router assembles all endpoint sub-routers.
    # Sub-routers declare their own full paths (e.g. /api/v1/health) so
    # no additional prefix is added here.
    app.include_router(router)

    # ── Static Files ──────────────────────────────────────────────────────────
    from fastapi.staticfiles import StaticFiles
    from pathlib import Path
    static_dir = Path(__file__).resolve().parent.parent / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    (static_dir / "uploads").mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    return app


# ─────────────────────────────────────────────────────────────────────────────
# ASGI app instance — referenced by uvicorn as "app.main:app"
# ─────────────────────────────────────────────────────────────────────────────

app: FastAPI = create_app()
