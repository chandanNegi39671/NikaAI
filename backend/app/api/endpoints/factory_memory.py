"""
backend/app/api/endpoints/factory_memory.py
───────────────────────────────────────────
Endpoints for defect pattern library & factory memory guidelines.
"""

from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.factory_memory import get_factory_memories

router = APIRouter(
    prefix="/api/v1/factory-memory",
    tags=["Factory Memory"],
)

@router.get("")
def list_patterns(query: str | None = None, db: Session = Depends(get_db)):
    """Search or list historical defect classes, recurring defect patterns, and recommended actions."""
    return get_factory_memories(db, query)
