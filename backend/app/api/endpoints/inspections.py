"""
backend/app/api/endpoints/inspections.py
───────────────────────────────────────
Endpoints for managing historical inspections.
"""

from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.db_models import Inspection

router = APIRouter(
    prefix="/api/v1/inspections",
    tags=["Inspections"],
)

@router.get("")
def list_inspections(
    status_filter: str | None = None,
    machine_id: str | None = None,
    worker_id: str | None = None,
    shift_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Retrieve historical inspection sessions with pagination and multi-variable filtering."""
    q = db.query(Inspection).filter(Inspection.is_deleted == False)
    
    if status_filter:
        q = q.filter(Inspection.status == status_filter.upper())
    if machine_id:
        q = q.filter(Inspection.machine_id == machine_id)
    if worker_id:
        q = q.filter(Inspection.worker_id == worker_id)
    if shift_id:
        q = q.filter(Inspection.shift_id == shift_id)
        
    total = q.count()
    inspections = q.order_by(Inspection.created_at.desc()).offset(offset).limit(limit).all()
    
    data = []
    for ins in inspections:
        data.append({
            "id": ins.id,
            "session_id": ins.session.session_id if ins.session else "N/A",
            "timestamp": ins.created_at.strftime("%b %d, %I:%M:%S %p"),
            "status": ins.status,
            "image_path": ins.image_path,
            "original_image_name": ins.original_image_name,
            "latency_ms": ins.latency_ms,
            "inference_time_ms": ins.inference_time_ms,
            "confidence": ins.confidence,
            "machine_name": ins.machine.name if ins.machine else "Unknown",
            "worker_name": ins.worker.name if ins.worker else "Unknown",
            "detections": [
                {
                    "class": d.defect_class,
                    "confidence": d.confidence,
                    "bounding_box": {"x1": d.x1, "y1": d.y1, "x2": d.x2, "y2": d.y2}
                } for d in ins.detections
            ]
        })
        
    return {"total": total, "results": data}

@router.get("/{id}")
def get_inspection(id: str, db: Session = Depends(get_db)):
    """Retrieve details for a specific inspection, including bounding boxes and Gemma explanations."""
    ins = db.query(Inspection).filter(Inspection.id == id, Inspection.is_deleted == False).first()
    if not ins:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection with ID {id} not found."
        )
        
    return {
        "id": ins.id,
        "session_id": ins.session.session_id if ins.session else "N/A",
        "timestamp": ins.created_at.strftime("%b %d, %I:%M:%S %p"),
        "status": ins.status,
        "image_path": ins.image_path,
        "original_image_name": ins.original_image_name,
        "latency_ms": ins.latency_ms,
        "inference_time_ms": ins.inference_time_ms,
        "confidence": ins.confidence,
        "machine_name": ins.machine.name if ins.machine else "Unknown",
        "worker_name": ins.worker.name if ins.worker else "Unknown",
        "detections": [
            {
                "class": d.defect_class,
                "confidence": d.confidence,
                "bounding_box": {"x1": d.x1, "y1": d.y1, "x2": d.x2, "y2": d.y2}
            } for d in ins.detections
        ],
        "explanation": {
            "gemma_explanation": ins.explanation.gemma_explanation if ins.explanation else "N/A",
            "trust_score": ins.explanation.trust_score if ins.explanation else 1.0,
            "explanation_json": ins.explanation.explanation_json if ins.explanation else None
        } if ins.explanation else None
    }

@router.delete("/{id}")
def delete_inspection(id: str, db: Session = Depends(get_db)):
    """Soft-delete an inspection from visual timelines and dashboards."""
    ins = db.query(Inspection).filter(Inspection.id == id, Inspection.is_deleted == False).first()
    if not ins:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection with ID {id} not found."
        )
    ins.is_deleted = True
    db.commit()
    return {"success": True, "detail": "Inspection soft-deleted successfully."}
