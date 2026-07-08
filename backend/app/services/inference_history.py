"""
backend/app/services/inference_history.py
─────────────────────────────────────────
Inference History Service for querying and filtering visual inspection logs.
"""

from sqlalchemy.orm import Session
from app.core.repository import inspection_repo
from app.core.logging import get_logger

logger = get_logger(__name__)

def list_inference_history(
    db: Session,
    machine_id: str | None = None,
    worker_id: str | None = None,
    shift_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    min_confidence: float | None = None,
    defect_class: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_dir: str = "desc"
) -> dict:
    """Query, filter, and paginate through historical YOLOv8 inspections in the database."""
    logger.info(f"Listing inference history with offset={offset}, limit={limit}")
    
    results, total_count = inspection_repo.list_with_full_filters(
        db,
        machine_id=machine_id,
        worker_id=worker_id,
        shift_id=shift_id,
        date_from=date_from,
        date_to=date_to,
        min_confidence=min_confidence,
        defect_class=defect_class,
        status=status,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_dir=sort_dir
    )
    
    formatted_results = []
    for ins in results:
        # Load associated details for the API client
        formatted_results.append({
            "id": ins.id,
            "session_id": ins.session_id,
            "machine_id": ins.machine_id,
            "machine_name": ins.machine.name if ins.machine else None,
            "worker_name": ins.worker.name if ins.worker else None,
            "shift_name": ins.shift.name if ins.shift else None,
            "image_path": ins.image_path,
            "status": ins.status,
            "confidence": ins.confidence,
            "inference_time_ms": ins.inference_time_ms,
            "created_at": ins.created_at.isoformat() if ins.created_at else None,
            "detections": [
                {
                    "defect_class": det.defect_class,
                    "confidence": det.confidence,
                    "bounding_box": {
                        "x1": det.x1,
                        "y1": det.y1,
                        "x2": det.x2,
                        "y2": det.y2
                    }
                }
                for det in ins.detections if not det.is_deleted
            ]
        })
        
    return {
        "total": total_count,
        "results": formatted_results,
        "limit": limit,
        "offset": offset
    }
