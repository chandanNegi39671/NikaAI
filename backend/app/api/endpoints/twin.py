"""
backend/app/api/endpoints/twin.py
──────────────────────────────────
Endpoints for Digital Twin spatial layout maps and real-time statuses.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.db_models import Machine
from app.core.auth import PermissionChecker

router = APIRouter(
    prefix="/api/v1/twin",
    tags=["Digital Twin"],
    dependencies=[Depends(PermissionChecker("inspection:read"))]
)

@router.get("/layout", summary="Retrieve spatial layout of the factory floor")
def get_digital_twin_layout(db: Session = Depends(get_db)):
    """Fetch physical coordinate map, production lines, and live statuses of line machines."""
    machines = db.query(Machine).filter(Machine.is_deleted == False).all()
    
    # Mocking coordinates for spatial rendering on the frontend
    layout_data = []
    for i, m in enumerate(machines):
        layout_data.append({
            "machine_id": m.id,
            "name": m.name,
            "status": m.status,
            "model_number": m.model_number,
            "coordinates": {
                "x": 120 * (i + 1),
                "y": 180
            },
            "production_line": f"Line {chr(65 + (i % 3))}"
        })
        
    return {
        "factory_name": "Nika AI Assembly Plant Alpha",
        "grid_size": {"width": 1000, "height": 800},
        "machines": layout_data
    }
