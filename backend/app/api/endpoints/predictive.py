"""
backend/app/api/endpoints/predictive.py
────────────────────────────────────────
Endpoints for Predictive Maintenance machine health analytics.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import PermissionChecker
from app.core.database import get_db
from app.services.predictive_maintenance import calculate_machine_health

router = APIRouter(
    prefix="/api/v1/predictive",
    tags=["Predictive Maintenance"],
    dependencies=[Depends(PermissionChecker("inspection:read"))],
)


@router.get(
    "/health/{machine_id}", summary="Get machine health diagnostics & failure risks"
)
def get_machine_predictive_health(machine_id: str, db: Session = Depends(get_db)):
    """Evaluate machine logs to estimate remaining useful life (RUL) and schedule maintenance."""
    health = calculate_machine_health(db, machine_id)
    if "status" in health and health["status"] == "error":
        raise HTTPException(status_code=404, detail=health["message"])
    return health
