"""
backend/app/api/endpoints/sync.py
──────────────────────────────────
Endpoints for Offline Edge node database batch synchronization.
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import PermissionChecker
from app.core.database import get_db
from app.models.db_models import Detection, Inspection

router = APIRouter(
    prefix="/api/v1/sync",
    tags=["Offline Edge Sync"],
    dependencies=[Depends(PermissionChecker("inspection:write"))],
)


class DetectionSync(BaseModel):
    defect_class: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float


class InspectionSync(BaseModel):
    offline_id: str
    timestamp: datetime
    machine_id: str | None = None
    worker_id: str | None = None
    status: str
    confidence: float
    inference_time_ms: float
    detections: List[DetectionSync]


@router.post("/upload", summary="Batch upload offline edge inspection logs")
def upload_edge_sync_logs(payload: List[InspectionSync], db: Session = Depends(get_db)):
    """Ingest inspection log payloads synchronized from offline edge nodes."""
    if not payload:
        return {"success": True, "synced_records_count": 0, "detail": "Empty payload."}

    successful_syncs = 0
    try:
        for ins in payload:
            # Check if already synced (idempotency guard) — no DB write, just a query
            edge_key = f"edge_sync_{ins.offline_id}"
            exists = (
                db.query(Inspection)
                .filter(Inspection.original_image_name == edge_key)
                .first()
            )
            if exists:
                continue

            db_ins = Inspection(
                machine_id=ins.machine_id,
                worker_id=ins.worker_id,
                status=ins.status,
                confidence=ins.confidence,
                inference_time_ms=ins.inference_time_ms,
                original_image_name=edge_key,
                created_at=ins.timestamp,
            )
            db.add(db_ins)
            # Flush to assign the auto-generated PK without committing the transaction
            db.flush()

            # Batch-add all detections for this inspection
            detection_objects = [
                Detection(
                    inspection_id=db_ins.id,
                    defect_class=det.defect_class,
                    confidence=det.confidence,
                    x1=det.x1,
                    y1=det.y1,
                    x2=det.x2,
                    y2=det.y2,
                )
                for det in ins.detections
            ]
            db.add_all(detection_objects)
            successful_syncs += 1

        # Single commit for the entire batch — atomic; rolls back all on error
        db.commit()

        return {
            "success": True,
            "synced_records_count": successful_syncs,
            "detail": f"Successfully synchronized {successful_syncs} offline edge inspections.",
        }
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync protocol failed: {exc}",
        )
