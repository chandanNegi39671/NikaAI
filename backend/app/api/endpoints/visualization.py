"""
backend/app/api/endpoints/visualization.py
──────────────────────────────────────────
Endpoints for the Generic Visualization Engine (previously Explainability).
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import PermissionChecker
from app.core.database import get_db
from app.services.visualization_engine import get_visualization_report

router = APIRouter(
    prefix="/api/v1/visualization",
    tags=["Visualization Engine"],
    dependencies=[Depends(PermissionChecker("inspection:read"))],
)

# ── Pydantic Schemas ──────────────────────────────────────────────────────────


class HeatmapRegionSchema(BaseModel):
    region_id: str
    x: float
    y: float
    radius: float
    intensity: float
    label: str


class ModelMetadataSchema(BaseModel):
    model_architecture: str
    weights_version: str
    classes: List[str]


class VisualizationReportSchema(BaseModel):
    inspection_id: str
    status: str
    overall_confidence: float
    inference_latency_ms: float
    trust_score: float
    explanation: str
    structured_reasoning: dict
    visualization_type: str = Field(
        "simulated_explainability", description="Type of visual map generated"
    )
    heatmap_regions: List[HeatmapRegionSchema]
    model_metadata: ModelMetadataSchema


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get(
    "/report/{inspection_id}",
    response_model=VisualizationReportSchema,
    summary="Get visual diagnostic heatmap and reasoning report",
)
def query_visualization_report(inspection_id: str, db: Session = Depends(get_db)):
    """Retrieve bounding box overlay SVG coordinate mappings, trust score, and simulated visual defect diagnostics."""
    report = get_visualization_report(db, inspection_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inference record '{inspection_id}' not found.",
        )
    return report
