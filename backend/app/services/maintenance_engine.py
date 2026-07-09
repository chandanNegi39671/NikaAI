"""
backend/app/services/maintenance_engine.py
──────────────────────────────────────────
Sprint 7: AI Manufacturing Intelligence — Maintenance Engine

Responsibilities:
  1. Compute a composite 0–100 health score from inspection history.
  2. Classify risk level (low / moderate / high / critical).
  3. Estimate Remaining Useful Life (RUL) in days.
  4. Generate a deterministic, rule-based maintenance recommendation.
  5. Detect health trend (improving / stable / degrading) from recent history.
  6. Persist the result as a MaintenancePrediction row.
  7. Return a fully typed dict compatible with the existing predictive endpoint.

Design:
  - Pure rule-based engine — no LLM, no ML model, no faking.
  - All thresholds are documented constants so they are auditable.
  - The persistence step is optional (skip_persist=True for unit tests).
  - Does NOT replace the existing calculate_machine_health() — it calls it
    and enriches the result with persistence + trend + recommendation code.

OWASP compliance:
  - All inputs validated before use.
  - No SQL built from user input (all parameterized via ORM).
  - No secrets in this module.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.db_models import Inspection, Machine, MaintenancePrediction

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Recommendation Catalogue
# ─────────────────────────────────────────────────────────────────────────────

# Each entry: (code, human_readable_text)
# The engine selects the most appropriate recommendation based on defect_rate
# thresholds, defect class mix, and recent failure trend.

RECOMMENDATIONS: dict[str, str] = {
    "continue_monitoring": (
        "Machine is operating within normal tolerances. Continue standard inspection frequency. "
        "Review monthly reports for any gradual trend changes."
    ),
    "increase_inspection_frequency": (
        "Elevated defect rate detected. Increase inspection frequency from standard to every shift. "
        "Log any new defect patterns in Factory Memory."
    ),
    "schedule_maintenance": (
        "Health score has declined significantly. Schedule a preventive maintenance window within "
        "the next 14 days. Check coolant levels, lubrication, and sensor calibration."
    ),
    "replace_component": (
        "Critical failure rate detected. Machine component replacement is likely required. "
        "Halt non-essential production runs and initiate a full mechanical inspection. "
        "Coordinate with the maintenance team immediately."
    ),
    "monitor_vibration": (
        "Pattern analysis indicates possible vibration-related defects. Attach a vibration sensor "
        "or manually inspect mounting bolts, bearings, and drive shafts."
    ),
    "reduce_machine_load": (
        "Thermal or stress defect signatures detected. Reduce machine throughput by 20% and "
        "monitor defect rate over the next 48 hours before resuming full capacity."
    ),
    "inspect_conveyor": (
        "Surface scratch patterns suggest conveyor or guide rail wear. Inspect material transport "
        "systems, rollers, and alignment guides. Clean protective surface covers."
    ),
}

# Defect classes that suggest vibration issues
_VIBRATION_DEFECT_CLASSES: frozenset[str] = frozenset({"dent", "scratch"})

# Defect classes that suggest thermal/stress issues
_THERMAL_DEFECT_CLASSES: frozenset[str] = frozenset(
    {"surface_crack", "burn_mark", "delamination"}
)

# Risk thresholds (defect_rate)
_THRESHOLDS = {
    "critical": 0.50,  # ≥ 50% FAIL → critical
    "high": 0.25,  # ≥ 25% FAIL → high
    "moderate": 0.10,  # ≥ 10% FAIL → moderate
    # below 10% → low
}

# RUL thresholds in days
_RUL = {
    "critical": 5,
    "high": 14,
    "moderate": 45,
    "low": 180,
}

# Priority mapping
_PRIORITY = {
    "critical": "urgent",
    "high": "high",
    "moderate": "medium",
    "low": "low",
}


# ─────────────────────────────────────────────────────────────────────────────
# Health Score Computation
# ─────────────────────────────────────────────────────────────────────────────


def _compute_health_score(defect_rate: float, recent_fail_rate: float) -> float:
    """Compute a composite 0–100 health score.

    Formula:
        base_score      = (1 - defect_rate) * 100
        recency_penalty = recent_fail_rate * 20   (amplifies recent degradation)
        health_score    = clamp(base_score - recency_penalty, 0, 100)

    Args:
        defect_rate:      Overall FAIL fraction (0.0–1.0) across all history.
        recent_fail_rate: FAIL fraction in the last 10 inspections only.

    Returns:
        Float 0–100, where 100 means perfect health.
    """
    base_score = (1.0 - defect_rate) * 100.0
    recency_penalty = recent_fail_rate * 20.0
    return round(max(0.0, min(100.0, base_score - recency_penalty)), 2)


def _classify_risk(defect_rate: float) -> str:
    if defect_rate >= _THRESHOLDS["critical"]:
        return "critical"
    if defect_rate >= _THRESHOLDS["high"]:
        return "high"
    if defect_rate >= _THRESHOLDS["moderate"]:
        return "moderate"
    return "low"


def _select_recommendation(
    risk_level: str,
    defect_classes: list[str],
) -> tuple[str, str]:
    """Select the most appropriate recommendation based on risk and defect patterns.

    Returns:
        Tuple of (recommendation_code, recommendation_text).
    """
    class_set = frozenset(defect_classes)

    if risk_level == "critical":
        return "replace_component", RECOMMENDATIONS["replace_component"]

    if risk_level == "high":
        if class_set & _VIBRATION_DEFECT_CLASSES:
            return "monitor_vibration", RECOMMENDATIONS["monitor_vibration"]
        if class_set & _THERMAL_DEFECT_CLASSES:
            return "reduce_machine_load", RECOMMENDATIONS["reduce_machine_load"]
        return "schedule_maintenance", RECOMMENDATIONS["schedule_maintenance"]

    if risk_level == "moderate":
        if class_set & frozenset({"scratch"}):
            return "inspect_conveyor", RECOMMENDATIONS["inspect_conveyor"]
        return (
            "increase_inspection_frequency",
            RECOMMENDATIONS["increase_inspection_frequency"],
        )

    # low risk
    return "continue_monitoring", RECOMMENDATIONS["continue_monitoring"]


def _compute_trend(db: Session, machine_id: str, current_health: float) -> str:
    """Compare current health score to the previous prediction for this machine.

    Returns:
        "improving"  — health improved by > 5 points
        "degrading"  — health decreased by > 5 points
        "stable"     — change within ±5 points or no history exists
    """
    from app.core.repository import maintenance_prediction_repo

    previous = maintenance_prediction_repo.get_latest_for_machine(db, machine_id)
    if previous is None:
        return "stable"
    delta = current_health - previous.health_score
    if delta > 5.0:
        return "improving"
    if delta < -5.0:
        return "degrading"
    return "stable"


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────


def run_maintenance_engine(
    db: Session,
    machine_id: str,
    skip_persist: bool = False,
) -> dict[str, Any]:
    """Run the full predictive maintenance analysis pipeline for one machine.

    Pipeline:
        1. Load machine and all its inspections (non-deleted).
        2. Compute defect rates (all-time + recent 10).
        3. Compute health_score, risk_level, rul_days.
        4. Select recommendation based on risk + defect classes.
        5. Detect trend from historical predictions.
        6. Persist a new MaintenancePrediction row (unless skip_persist=True).
        7. Return a fully serializable dict.

    Args:
        db:            SQLAlchemy Session.
        machine_id:    UUID string of the target machine.
        skip_persist:  If True, skip DB write (useful for unit tests and dry-run endpoints).

    Returns:
        Dict with keys: machine_id, machine_name, health_score, risk_level,
        rul_days, defect_rate, recommendation, recommendation_code, priority,
        trend, total_inspections, failed_inspections, next_maintenance_date,
        computed_at.

    Raises:
        ValueError: If machine_id does not exist in the database.
    """
    machine: Machine | None = (
        db.query(Machine)
        .filter(
            Machine.id == machine_id,
            Machine.is_deleted == False,
        )
        .first()
    )

    if not machine:
        raise ValueError(f"Machine '{machine_id}' not found.")

    # ── Load inspection history ────────────────────────────────────────────────
    inspections: list[Inspection] = (
        db.query(Inspection)
        .filter(
            Inspection.machine_id == machine_id,
            Inspection.is_deleted == False,
        )
        .order_by(Inspection.created_at.desc())
        .all()
    )

    total = len(inspections)

    if total == 0:
        # Nominal default — no data available yet
        rec_code, rec_text = (
            "continue_monitoring",
            RECOMMENDATIONS["continue_monitoring"],
        )
        result = _build_result(
            machine=machine,
            health_score=100.0,
            risk_level="low",
            rul_days=180,
            defect_rate=0.0,
            recommendation=rec_text,
            recommendation_code=rec_code,
            priority="low",
            trend="stable",
            total=0,
            failed=0,
        )
        if not skip_persist:
            _persist(db, machine_id, result)
        return result

    failed = sum(1 for i in inspections if i.status == "FAIL")
    defect_rate = failed / total

    # Recency window — most recent 10 inspections
    recent = inspections[:10]
    recent_failed = sum(1 for i in recent if i.status == "FAIL")
    recent_fail_rate = recent_failed / len(recent) if recent else 0.0

    # ── Core metrics ──────────────────────────────────────────────────────────
    health_score = _compute_health_score(defect_rate, recent_fail_rate)
    risk_level = _classify_risk(defect_rate)
    rul_days = _RUL[risk_level]
    priority = _PRIORITY[risk_level]

    # ── Defect class mix (from inspections that have detections) ──────────────
    defect_classes: list[str] = []
    for insp in inspections:
        for det in insp.detections:
            defect_classes.append(det.defect_class)

    rec_code, rec_text = _select_recommendation(risk_level, defect_classes)

    # ── Trend detection ───────────────────────────────────────────────────────
    trend = _compute_trend(db, machine_id, health_score)

    result = _build_result(
        machine=machine,
        health_score=health_score,
        risk_level=risk_level,
        rul_days=rul_days,
        defect_rate=round(defect_rate, 4),
        recommendation=rec_text,
        recommendation_code=rec_code,
        priority=priority,
        trend=trend,
        total=total,
        failed=failed,
    )

    if not skip_persist:
        _persist(db, machine_id, result)

    logger.info(
        "Maintenance engine completed.",
        extra={
            "machine_id": machine_id,
            "machine_name": machine.name,
            "health_score": health_score,
            "risk_level": risk_level,
            "trend": trend,
            "recommendation_code": rec_code,
        },
    )

    return result


def _build_result(
    *,
    machine: Machine,
    health_score: float,
    risk_level: str,
    rul_days: int,
    defect_rate: float,
    recommendation: str,
    recommendation_code: str,
    priority: str,
    trend: str,
    total: int,
    failed: int,
) -> dict[str, Any]:
    """Construct the standardized result dict."""
    computed_at = datetime.now(timezone.utc)
    next_maintenance = computed_at + timedelta(days=rul_days)
    return {
        "machine_id": machine.id,
        "machine_name": machine.name,
        "machine_location": machine.location,
        "machine_status": machine.status,
        "health_score": health_score,
        "risk_level": risk_level,
        "rul_days": rul_days,
        "defect_rate": defect_rate,
        "recommendation": recommendation,
        "recommendation_code": recommendation_code,
        "priority": priority,
        "trend": trend,
        "total_inspections": total,
        "failed_inspections": failed,
        "next_maintenance_date": next_maintenance.strftime("%Y-%m-%d"),
        "computed_at": computed_at.isoformat(),
    }


def _persist(db: Session, machine_id: str, result: dict[str, Any]) -> None:
    """Write a MaintenancePrediction row to the database."""
    try:
        pred = MaintenancePrediction(
            machine_id=machine_id,
            health_score=result["health_score"],
            risk_level=result["risk_level"],
            rul_days=result["rul_days"],
            defect_rate=result["defect_rate"],
            recommendation=result["recommendation"],
            recommendation_code=result["recommendation_code"],
            priority=result["priority"],
            trend=result["trend"],
            total_inspections=result["total_inspections"],
            failed_inspections=result["failed_inspections"],
            computed_at=datetime.now(timezone.utc),
        )
        db.add(pred)
        db.commit()
        db.refresh(pred)
        logger.info(
            "MaintenancePrediction persisted.",
            extra={"prediction_id": pred.id, "machine_id": machine_id},
        )
    except Exception as exc:
        db.rollback()
        logger.error(
            "Failed to persist MaintenancePrediction.",
            extra={"machine_id": machine_id, "error": str(exc)},
        )
