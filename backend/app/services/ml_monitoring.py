"""
backend/app/services/ml_monitoring.py
──────────────────────────────────────
Machine Learning Model Drift & Quality Performance Monitoring Service.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.db_models import Inspection
from app.core.logging import get_logger

logger = get_logger(__name__)

# Baseline parameters (e.g. established during staging/validation validation)
BASELINE_CONFIDENCE = 0.82
BASELINE_REJECT_RATE = 0.15

def analyze_ml_performance(db: Session, limit: int = 100) -> dict:
    """Analyze recent inspection metrics to detect performance drift or model decay."""
    try:
        # Fetch the most recent N inspections
        recent_inspections = db.query(Inspection).filter(
            Inspection.is_deleted == False
        ).order_by(Inspection.created_at.desc()).limit(limit).all()
        
        if not recent_inspections:
            return {"status": "insufficient_data"}
            
        total = len(recent_inspections)
        avg_confidence = sum(ins.confidence for ins in recent_inspections) / total
        
        rejects = sum(1 for ins in recent_inspections if ins.status == "FAIL")
        reject_rate = rejects / total
        
        # Calculate drift offsets
        confidence_drift = BASELINE_CONFIDENCE - avg_confidence
        reject_rate_drift = reject_rate - BASELINE_REJECT_RATE
        
        # Determine status
        status = "healthy"
        warnings = []
        
        # Warning if average confidence drops significantly (> 10%)
        if confidence_drift > 0.10:
            status = "degraded"
            warnings.append("Confidence drift detected: Model predictions show decreased accuracy.")
            
        # Warning if reject rate deviates drastically from normal bounds (> 15% deviation)
        if abs(reject_rate_drift) > 0.15:
            status = "degraded"
            warnings.append("Reject rate drift detected: Production inputs might have changed.")

        metrics = {
            "status": status,
            "sample_size": total,
            "current_avg_confidence": round(avg_confidence, 4),
            "baseline_avg_confidence": BASELINE_CONFIDENCE,
            "confidence_drift": round(confidence_drift, 4),
            "current_reject_rate": round(reject_rate, 4),
            "baseline_reject_rate": BASELINE_REJECT_RATE,
            "reject_rate_drift": round(reject_rate_drift, 4),
            "warnings": warnings
        }
        
        logger.info(f"ML monitoring analysis completed. Status: {status}")
        return metrics
    except Exception as exc:
        logger.error(f"Failed to analyze ML performance metrics: {exc}")
        return {"status": "error", "message": str(exc)}
