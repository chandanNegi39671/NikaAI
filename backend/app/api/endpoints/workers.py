"""
backend/app/api/endpoints/workers.py
───────────────────────────────────
Endpoints for managing factory workers and shifts.
"""

from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.db_models import Worker, Shift
from app.core.auth import PermissionChecker

router = APIRouter(
    prefix="/api/v1/workers",
    tags=["Workers & Shifts"],
    dependencies=[Depends(PermissionChecker("inspection:read"))]
)

@router.get("")
def list_workers(db: Session = Depends(get_db)):
    """Retrieve list of active workers."""
    workers = db.query(Worker).filter(Worker.is_deleted == False).all()
    return [
        {
            "id": w.id,
            "name": w.name,
            "employee_code": w.employee_code,
            "role": w.role
        } for w in workers
    ]

@router.get("/shifts")
def list_shifts(db: Session = Depends(get_db)):
    """Retrieve active work shifts and assigned workers."""
    shifts = db.query(Shift).filter(Shift.is_deleted == False).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "worker_name": s.worker.name if s.worker else "Unassigned"
        } for s in shifts
    ]
