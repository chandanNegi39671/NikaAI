"""
backend/app/api/endpoints/inference_history.py
─────────────────────────────────────────────
Endpoints for querying and filtering paginated inspection logs.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import PermissionChecker
from app.core.database import get_db
from app.services.inference_history import list_inference_history

router = APIRouter(
    prefix="/api/v1/inference",
    tags=["Inference History"],
    dependencies=[Depends(PermissionChecker("inspection:read"))],
)

# ── Pydantic Schemas ──────────────────────────────────────────────────────────


class DetectionDetailSchema(BaseModel):
    defect_class: str
    confidence: float
    bounding_box: dict


class InferenceLogSchema(BaseModel):
    id: str
    session_id: Optional[str] = None
    machine_id: Optional[str] = None
    machine_name: Optional[str] = None
    worker_name: Optional[str] = None
    shift_name: Optional[str] = None
    image_path: Optional[str] = None
    status: str
    confidence: float
    inference_time_ms: float
    created_at: Optional[str] = None
    detections: List[DetectionDetailSchema]


class InferenceHistoryResponse(BaseModel):
    total: int
    results: List[InferenceLogSchema]
    limit: int
    offset: int


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get(
    "/history",
    response_model=InferenceHistoryResponse,
    summary="Query paginated inspection logs",
)
def query_inference_history(
    machine_id: Optional[str] = None,
    worker_id: Optional[str] = None,
    shift_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    min_confidence: Optional[float] = None,
    defect_class: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    db: Session = Depends(get_db),
):
    """Retrieve filtered, paginated visual inspections registered on the line."""
    logs = list_inference_history(
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
        sort_dir=sort_dir,
    )
    return logs


@router.get(
    "/history/{inspection_id}",
    response_model=InferenceLogSchema,
    summary="Get inspection details",
)
def get_single_inference_detail(inspection_id: str, db: Session = Depends(get_db)):
    """Retrieve complete YOLOv8 detection results, confidence, and context logs for a specific inspection."""
    from app.core.repository import inspection_repo

    ins = inspection_repo.get(db, inspection_id)
    if not ins:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection record '{inspection_id}' not found.",
        )

    return {
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
                    "y2": det.y2,
                },
            }
            for det in ins.detections
            if not det.is_deleted
        ],
    }
