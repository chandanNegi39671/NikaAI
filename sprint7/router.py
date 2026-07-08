"""
backend/app/api/router.py
──────────────────────────
Top-level versioned API router for Nika AI.

This module is the single assembly point for every sub-router in the
API layer.  ``main.py`` imports one symbol — ``router`` — and calls
``app.include_router(router)``.

Versioning strategy:
  All routes are prefixed with ``/api/v1``.  When v2 endpoints are
  introduced they get their own ``APIRouter(prefix="/api/v2")`` and are
  included below without touching existing v1 routes.

Adding a new endpoint group:
  1. Create ``app/api/endpoints/<name>.py`` with a local ``router``.
  2. Import it here and add ``router.include_router(<name>.router)``.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.endpoints.health import router as health_router
from app.api.endpoints.prediction import router as prediction_router
from app.api.endpoints.inspections import router as inspections_router
from app.api.endpoints.analytics import router as analytics_router
from app.api.endpoints.factory_memory import router as factory_memory_router
from app.api.endpoints.machines import router as machines_router
from app.api.endpoints.workers import router as workers_router
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.websocket import router as websocket_router
from app.api.endpoints.models import router as models_router
from app.api.endpoints.explainability import router as explainability_router
from app.api.endpoints.assistant import router as assistant_router
from app.api.endpoints.predictive import router as predictive_router
from app.api.endpoints.twin import router as twin_router
from app.api.endpoints.sync import router as sync_router
from app.api.endpoints.notifications import router as notifications_router

# ─────────────────────────────────────────────────────────────────────────────
# Versioned root router
# All endpoints sit under /api/v1 when included in main.py with prefix=""
# (main.py does: app.include_router(router) — no extra prefix needed here
#  because each sub-router declares its own full path).
# ─────────────────────────────────────────────────────────────────────────────

router = APIRouter()

# Register sub-routers — order determines Swagger UI display order.
# NOTE: Each sub-router declares its own full /api/v1/<path> prefix.
router.include_router(auth_router)
router.include_router(health_router)
router.include_router(prediction_router)
router.include_router(inspections_router)
router.include_router(analytics_router)
router.include_router(factory_memory_router)
router.include_router(machines_router)
router.include_router(workers_router)
router.include_router(websocket_router)
router.include_router(models_router)
router.include_router(explainability_router)
router.include_router(assistant_router)
router.include_router(predictive_router)
router.include_router(twin_router)
router.include_router(sync_router)
router.include_router(notifications_router)
