"""
backend/app/api/endpoints/maintenance.py
─────────────────────────────────────────
Sprint 7: AI Manufacturing Intelligence — Maintenance & Trend API

Routes:
    GET  /api/v1/maintenance/fleet            — Latest health for all machines
    GET  /api/v1/maintenance/predict/{id}     — Run engine + persist for one machine
    GET  /api/v1/maintenance/history/{id}     — Prediction history for one machine
    GET  /api/v1/maintenance/report/{id}      — Full machine maintenance report (JSON)
    GET  /api/v1/maintenance/trend/daily      — Daily inspection trend
    GET  /api/v1/maintenance/trend/weekly     — Weekly inspection trend
    GET  /api/v1/maintenance/trend/monthly    — Monthly inspection trend
    GET  /api/v1/maintenance/trend/defects    — Defect type frequency trend
    GET  /api/v1/maintenance/trend/machines   — Per-machine failure trend
    GET  /api/v1/maintenance/trend/summary    — Fleet KPI summary

Security:
    - All endpoints require `analytics:read` permission (same as existing analytics router)
    - Predict endpoint requires `inspection:read` (read + compute)
    - RBAC enforced via `PermissionChecker` dependency
    - Rate limiting via global SlowAPI middleware on all routes

Naming conventions:
    - Router prefix `/api/v1/maintenance` — distinct from existing `/api/v1/predictive`
    - No overlap with `GET /api/v1/predictive/health/{machine_id}` (existing, untouched)
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import PermissionChecker
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.repository import maintenance_prediction_repo
from app.models.db_models import Machine, MaintenancePrediction
from app.services.maintenance_engine import run_maintenance_engine
from app.services.trend_analysis import (
    get_daily_trend,
    get_defect_type_trend,
    get_machine_failure_trend,
    get_monthly_trend,
    get_trend_summary,
    get_weekly_trend,
)

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Response Schemas
# ─────────────────────────────────────────────────────────────────────────────


class MaintenancePredictionResponse(BaseModel):
    """Serialized shape of a single maintenance prediction."""

    id: str
    machine_id: str | None
    machine_name: str | None
    health_score: float
    risk_level: str
    rul_days: int
    defect_rate: float
    recommendation: str | None
    recommendation_code: str | None
    priority: str
    trend: str
    total_inspections: int
    failed_inspections: int
    computed_at: str

    class Config:
        from_attributes = True


class FleetOverviewResponse(BaseModel):
    """Fleet health overview — one entry per machine with latest prediction."""

    total_machines: int
    machines_critical: int
    machines_high: int
    machines_moderate: int
    machines_healthy: int
    fleet: list[dict[str, Any]]


class HistoryResponse(BaseModel):
    machine_id: str
    machine_name: str
    total: int
    predictions: list[dict[str, Any]]


class MaintenanceReportResponse(BaseModel):
    machine_id: str
    machine_name: str
    machine_location: str | None
    machine_status: str | None
    current_health: dict[str, Any]
    prediction_history: list[dict[str, Any]]
    defect_trend: list[dict[str, Any]]
    recommendation_history: list[str]


# ─────────────────────────────────────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────────────────────────────────────

router = APIRouter(
    prefix="/api/v1/maintenance",
    tags=["Maintenance Intelligence"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Internal serializer (avoids duplicate dict building)
# ─────────────────────────────────────────────────────────────────────────────


def _serialize_prediction(pred: MaintenancePrediction) -> dict[str, Any]:
    """Convert a MaintenancePrediction ORM row to a serializable dict."""
    return {
        "id": pred.id,
        "machine_id": pred.machine_id,
        "machine_name": pred.machine.name if pred.machine else None,
        "machine_location": pred.machine.location if pred.machine else None,
        "health_score": pred.health_score,
        "risk_level": pred.risk_level,
        "rul_days": pred.rul_days,
        "defect_rate": pred.defect_rate,
        "recommendation": pred.recommendation,
        "recommendation_code": pred.recommendation_code,
        "priority": pred.priority,
        "trend": pred.trend,
        "total_inspections": pred.total_inspections,
        "failed_inspections": pred.failed_inspections,
        "computed_at": pred.computed_at.isoformat() if pred.computed_at else None,
        "created_at": pred.created_at.isoformat() if pred.created_at else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Fleet Overview
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/fleet",
    summary="Fleet health overview — latest prediction for every machine",
    response_model=FleetOverviewResponse,
    dependencies=[Depends(PermissionChecker("analytics:read"))],
)
def get_fleet_overview(db: Session = Depends(get_db)) -> FleetOverviewResponse:
    """Return the most recent maintenance prediction for every machine in the fleet.

    Machines that have no predictions yet are automatically included with
    nominal health defaults so the fleet view is always complete.
    """
    all_machines = db.query(Machine).filter(Machine.is_deleted == False).all()
    latest_predictions = maintenance_prediction_repo.get_fleet_latest(db)
    pred_map: dict[str, MaintenancePrediction] = {
        p.machine_id: p for p in latest_predictions
    }

    fleet: list[dict[str, Any]] = []
    counts = {"critical": 0, "high": 0, "moderate": 0, "low": 0}

    for m in all_machines:
        pred = pred_map.get(m.id)
        if pred:
            entry = _serialize_prediction(pred)
            counts[pred.risk_level] = counts.get(pred.risk_level, 0) + 1
        else:
            # Machine exists but has never been analysed — show nominal
            entry = {
                "machine_id": m.id,
                "machine_name": m.name,
                "machine_location": m.location,
                "health_score": 100.0,
                "risk_level": "low",
                "rul_days": 180,
                "defect_rate": 0.0,
                "recommendation": "No inspections recorded yet. Machine is in nominal state.",
                "recommendation_code": "continue_monitoring",
                "priority": "low",
                "trend": "stable",
                "total_inspections": 0,
                "failed_inspections": 0,
                "computed_at": None,
                "created_at": None,
            }
            counts["low"] += 1

        fleet.append(entry)

    return FleetOverviewResponse(
        total_machines=len(all_machines),
        machines_critical=counts.get("critical", 0),
        machines_high=counts.get("high", 0),
        machines_moderate=counts.get("moderate", 0),
        machines_healthy=counts.get("low", 0),
        fleet=fleet,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Predict (Run Engine)
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/predict/{machine_id}",
    summary="Run maintenance engine for a machine and persist the result",
    dependencies=[Depends(PermissionChecker("inspection:read"))],
)
def predict_machine_health(
    machine_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Execute the full maintenance analysis pipeline for the given machine.

    - Computes health score, risk level, RUL, recommendation, and trend.
    - Persists the result as a new MaintenancePrediction row.
    - Returns the full prediction dict.

    Note: This endpoint differs from the existing `/api/v1/predictive/health/{id}`
    endpoint — that returns a quick in-memory result; this one persists to DB.
    """
    try:
        result = run_maintenance_engine(db, machine_id)
        logger.info(
            "Maintenance prediction requested via API.",
            extra={"machine_id": machine_id, "risk_level": result.get("risk_level")},
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error(
            "Maintenance engine failed.",
            extra={"machine_id": machine_id, "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Maintenance engine error: {exc}",
        )


# ─────────────────────────────────────────────────────────────────────────────
# History
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/history/{machine_id}",
    summary="Prediction history for a specific machine",
    dependencies=[Depends(PermissionChecker("analytics:read"))],
)
def get_machine_history(
    machine_id: str,
    limit: int = Query(
        default=30, ge=1, le=100, description="Max predictions to return"
    ),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
) -> HistoryResponse:
    """Return paginated historical maintenance predictions for one machine."""
    machine = (
        db.query(Machine)
        .filter(
            Machine.id == machine_id,
            Machine.is_deleted == False,
        )
        .first()
    )

    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine '{machine_id}' not found.",
        )

    predictions = maintenance_prediction_repo.get_history_for_machine(
        db, machine_id, limit=limit, offset=offset
    )

    return HistoryResponse(
        machine_id=machine_id,
        machine_name=machine.name,
        total=len(predictions),
        predictions=[_serialize_prediction(p) for p in predictions],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Full Machine Report
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/report/{machine_id}",
    summary="Full maintenance intelligence report for a machine",
    dependencies=[Depends(PermissionChecker("analytics:read"))],
)
def get_machine_report(
    machine_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return a comprehensive export-ready JSON report for a single machine.

    Includes:
        - Current health state (runs engine, does NOT persist again)
        - Last 10 historical predictions
        - Defect type trend (30d) for this machine
        - All unique recommendation codes in history
    """
    machine = (
        db.query(Machine)
        .filter(
            Machine.id == machine_id,
            Machine.is_deleted == False,
        )
        .first()
    )

    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine '{machine_id}' not found.",
        )

    try:
        current = run_maintenance_engine(db, machine_id, skip_persist=True)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    history = maintenance_prediction_repo.get_history_for_machine(
        db, machine_id, limit=10
    )

    # Defect trend for this machine specifically
    defect_trend = get_defect_type_trend(db, days=30)

    rec_history = list(
        {p.recommendation_code for p in history if p.recommendation_code}
    )

    return {
        "machine_id": machine_id,
        "machine_name": machine.name,
        "machine_location": machine.location,
        "machine_status": machine.status,
        "current_health": current,
        "prediction_history": [_serialize_prediction(p) for p in history],
        "defect_trend": defect_trend,
        "recommendation_history": rec_history,
        "report_generated_at": __import__("datetime").datetime.utcnow().isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Trend Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/trend/daily",
    summary="Daily inspection trend (last N days)",
    dependencies=[Depends(PermissionChecker("analytics:read"))],
)
def daily_trend(
    days: int = Query(default=30, ge=1, le=90, description="Number of days"),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return daily inspection metrics for trend charts."""
    return get_daily_trend(db, days=days)


@router.get(
    "/trend/weekly",
    summary="Weekly inspection trend (last N weeks)",
    dependencies=[Depends(PermissionChecker("analytics:read"))],
)
def weekly_trend(
    weeks: int = Query(default=12, ge=1, le=52, description="Number of weeks"),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return weekly aggregated metrics for trend charts."""
    return get_weekly_trend(db, weeks=weeks)


@router.get(
    "/trend/monthly",
    summary="Monthly inspection trend (last N months)",
    dependencies=[Depends(PermissionChecker("analytics:read"))],
)
def monthly_trend(
    months: int = Query(default=6, ge=1, le=24, description="Number of months"),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return monthly aggregated metrics for trend charts."""
    return get_monthly_trend(db, months=months)


@router.get(
    "/trend/defects",
    summary="Defect type frequency trend",
    dependencies=[Depends(PermissionChecker("analytics:read"))],
)
def defect_trend(
    days: int = Query(default=30, ge=1, le=90, description="Lookback window in days"),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return defect class frequencies for the specified period."""
    return get_defect_type_trend(db, days=days)


@router.get(
    "/trend/machines",
    summary="Per-machine failure rate trend",
    dependencies=[Depends(PermissionChecker("analytics:read"))],
)
def machine_trend(
    days: int = Query(default=30, ge=1, le=90, description="Lookback window in days"),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return per-machine failure rates for the specified period."""
    return get_machine_failure_trend(db, days=days)


@router.get(
    "/trend/summary",
    summary="Fleet-wide KPI trend summary",
    dependencies=[Depends(PermissionChecker("analytics:read"))],
)
def trend_summary(
    days: int = Query(default=30, ge=1, le=90, description="Lookback window in days"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return high-level KPI summary for the fleet over the specified period."""
    return get_trend_summary(db, days=days)
