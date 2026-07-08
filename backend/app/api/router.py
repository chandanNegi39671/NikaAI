"""
backend/app/api/router.py
──────────────────────────
Top-level versioned API router for Nika AI.
Assembles every endpoint sub-router in the API layer.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.health import router as health_router
from app.api.endpoints.prediction import router as prediction_router
from app.api.endpoints.inspections import router as inspections_router
from app.api.endpoints.analytics import router as analytics_router
from app.api.endpoints.factory_memory import router as factory_memory_router
from app.api.endpoints.machines import router as machines_router
from app.api.endpoints.workers import router as workers_router
from app.api.endpoints.websocket import router as websocket_router
from app.api.endpoints.models import router as models_router
from app.api.endpoints.visualization import router as visualization_router # Sprint 8 Visualizations
from app.api.endpoints.assistant import router as assistant_router
from app.api.endpoints.predictive import router as predictive_router
from app.api.endpoints.twin import router as twin_router
from app.api.endpoints.sync import router as sync_router
from app.api.endpoints.maintenance import router as maintenance_router
from app.api.endpoints.inference_history import router as inference_history_router # Sprint 8 History
from app.api.endpoints.audit_logs import router as audit_logs_router # Sprint 8 Audit Logs

router = APIRouter()

# Register sub-routers — order determines Swagger UI display order.
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
router.include_router(visualization_router)
router.include_router(assistant_router)
router.include_router(predictive_router)
router.include_router(twin_router)
router.include_router(sync_router)
router.include_router(maintenance_router)
router.include_router(inference_history_router)
router.include_router(audit_logs_router)
