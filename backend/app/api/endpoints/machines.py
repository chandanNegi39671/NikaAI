"""
backend/app/api/endpoints/machines.py
────────────────────────────────────
Endpoints for managing factory machines.
"""

from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.db_models import Machine

router = APIRouter(
    prefix="/api/v1/machines",
    tags=["Machines"],
)

@router.get("")
def list_machines(db: Session = Depends(get_db)):
    """Retrieve list of industrial machines and their status."""
    machines = db.query(Machine).filter(Machine.is_deleted == False).all()
    return [
        {
            "id": m.id,
            "name": m.name,
            "model_number": m.model_number,
            "status": m.status,
            "location": m.location
        } for m in machines
    ]
