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
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import router  # single versioned router — all routes
from app.core.config import Environment, settings
from app.core.limiter import limiter
from app.core.logging import get_logger, setup_logging
from app.core.middleware import SecurityMiddleware
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
        raise

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
        logger.error(
            "Failed to initialise PredictionService during startup.",
            extra={"error": str(exc), "type": type(exc).__name__},
        )
        if settings.env == Environment.PRODUCTION:
            raise

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
    # Disable docs in production
    _is_production = settings.env == Environment.PRODUCTION

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "AI-powered manufacturing defect detection API. "
            "Upload an image to receive YOLOv8 defect detections with "
            "bounding boxes and confidence scores."
        ),
        # Always None — we serve docs manually below using unpkg CDN
        # to avoid blank-page issues with the default jsdelivr CDN.
        docs_url=None,
        redoc_url=None,
        openapi_url=None if _is_production else "/api/openapi.json",
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ── Middleware ────────────────────────────────────────────────────────────
    app.add_middleware(SecurityMiddleware)

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "Accept"],
    )

    # ── Routes ────────────────────────────────────────────────────────────────
    # The versioned router assembles all endpoint sub-routers.
    # Sub-routers declare their own full paths (e.g. /api/v1/health) so
    # no additional prefix is added here.
    app.include_router(router)

    # ── Custom Swagger UI (unpkg CDN — avoids blank page from jsdelivr) ───────
    # FastAPI's default Swagger loads assets from cdn.jsdelivr.net which can
    # be blocked or slow on some networks, producing a blank white page.
    # Serving from unpkg.com resolves this.
    if not _is_production:

        @app.get("/api/docs", include_in_schema=False)
        async def custom_swagger_ui():
            return get_swagger_ui_html(
                openapi_url="/api/openapi.json",
                title=f"{settings.app_name} - Swagger UI",
                swagger_js_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
                swagger_css_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css",
            )

        @app.get("/api/redoc", include_in_schema=False)
        async def custom_redoc():
            return get_redoc_html(
                openapi_url="/api/openapi.json",
                title=f"{settings.app_name} - ReDoc",
                redoc_js_url="https://unpkg.com/redoc@latest/bundles/redoc.standalone.js",
            )

    # ── Prometheus Metrics ───────────────────────────────────────────────────
    from app.core.metrics import metrics_app

    app.mount("/metrics", metrics_app)

    # ── OpenTelemetry Tracing ────────────────────────────────────────────────
    from app.core.telemetry import setup_telemetry

    setup_telemetry(app)

    # ── Static Files ──────────────────────────────────────────────────────────
    from pathlib import Path

    from fastapi.staticfiles import StaticFiles

    static_dir = Path(__file__).resolve().parent.parent / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    (static_dir / "uploads").mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # ── Custom OpenAPI schema ─────────────────────────────────────────────────
    from fastapi.openapi.utils import get_openapi

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Include detailed schema descriptions for standard enterprise HTTP errors
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        if "schemas" not in openapi_schema["components"]:
            openapi_schema["components"]["schemas"] = {}

        openapi_schema["components"]["schemas"]["ErrorSchema"] = {
            "title": "ErrorSchema",
            "type": "object",
            "properties": {
                "detail": {
                    "title": "Error Detail Description",
                    "type": "string",
                    "example": "Resource not found or validation error details.",
                }
            },
        }

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    return app


# ─────────────────────────────────────────────────────────────────────────────
# ASGI app instance — referenced by uvicorn as "app.main:app"
# ─────────────────────────────────────────────────────────────────────────────

app: FastAPI = create_app()
