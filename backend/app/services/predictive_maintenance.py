"""
backend/app/services/predictive_maintenance.py
──────────────────────────────────────────────
Predictive Maintenance Engine tracking Machine Failure Risk and Remaining Useful Life (RUL).
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.db_models import Inspection, Machine

logger = get_logger(__name__)


def calculate_machine_health(db: Session, machine_id: str) -> dict:
    """Evaluate machine telemetry and failure history to predict maintenance needs."""
    try:
        machine = db.query(Machine).filter(Machine.id == machine_id).first()
        if not machine:
            return {"status": "error", "message": f"Machine {machine_id} not found."}

        # Get total inspections for this machine
        inspections = (
            db.query(Inspection)
            .filter(Inspection.machine_id == machine_id, Inspection.is_deleted == False)
            .all()
        )

        if not inspections:
            return {
                "machine_name": machine.name,
                "risk_score": 10.0,
                "remaining_useful_life_days": 180,
                "status": "nominal",
                "next_maintenance_date": (datetime.now() + timedelta(days=90)).strftime(
                    "%Y-%m-%d"
                ),
                "reason": "No inspection logs registered yet. Nominal default state.",
            }

        total_runs = len(inspections)
        failed_runs = sum(1 for ins in inspections if ins.status == "FAIL")
        defect_rate = failed_runs / total_runs if total_runs > 0 else 0

        # Calculate Risk Score (0-100) based on defect rates and recent fail trends
        risk_score = min(100.0, max(0.0, (defect_rate * 150) + 10.0))

        # Estimate RUL (Remaining Useful Life in days)
        rul_days = max(5, int((1.0 - defect_rate) * 90))

        # Status assignment
        if risk_score > 70.0:
            status = "critical"
            reason = "High anomaly rates detected. Clamping alignment review suggested immediately."
        elif risk_score > 35.0:
            status = "warning"
            reason = "Moderate defect levels detected. Schedule inspection check soon."
        else:
            status = "nominal"
            reason = "Normal operation tolerances within nominal bounds."

        next_maintenance = datetime.now() + timedelta(days=rul_days)

        metrics = {
            "machine_id": machine_id,
            "machine_name": machine.name,
            "total_inspections": total_runs,
            "failed_inspections": failed_runs,
            "defect_rate": round(defect_rate, 4),
            "risk_score": round(risk_score, 2),
            "remaining_useful_life_days": rul_days,
            "status": status,
            "next_maintenance_date": next_maintenance.strftime("%Y-%m-%d"),
            "reason": reason,
        }

        logger.info(
            f"Predictive maintenance checked for '{machine.name}': Status={status}"
        )
        return metrics
    except Exception as exc:
        logger.error(
            f"Predictive maintenance check failed for machine {machine_id}: {exc}"
        )
        return {"status": "error", "message": str(exc)}
