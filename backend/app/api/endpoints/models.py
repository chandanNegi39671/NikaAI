"""
backend/app/api/endpoints/models.py
───────────────────────────────────
Endpoints for YOLOv8 model registry and runtime lifecycle status management.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import PermissionChecker
from app.core.database import get_db
from app.services.registry import model_registry

router = APIRouter(
    prefix="/api/v1/models",
    tags=["Model Registry"],
    dependencies=[Depends(PermissionChecker("admin"))],
)

# ── Pydantic Schemas ──────────────────────────────────────────────────────────


class ModelVersionSchema(BaseModel):
    id: str
    version_name: str
    file_path: Optional[str] = None
    deployment_status: str
    map_score: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    training_date: Optional[datetime] = None
    dataset_name: Optional[str] = None
    trained_by: Optional[str] = None
    framework: Optional[str] = None
    commit_hash: Optional[str] = None
    artifact_path: Optional[str] = None
    model_size_mb: Optional[float] = None
    parameter_count: Optional[int] = None
    parent_version: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ModelListResponse(BaseModel):
    models: List[ModelVersionSchema]


class ModelRegisterRequest(BaseModel):
    version_name: str = Field(
        ..., description="Unique filename/version of the weights file"
    )
    file_path: Optional[str] = Field(
        None, description="Absolute file path on server disk"
    )
    deployment_status: str = Field(
        "staging", description="Initial status: staging | training | validated"
    )
    map_score: Optional[float] = Field(0.90, description="mAP evaluation metric")
    precision: Optional[float] = Field(0.90, description="Precision evaluation metric")
    recall: Optional[float] = Field(0.90, description="Recall evaluation metric")
    dataset_name: Optional[str] = Field(
        "General-Nika", description="Dataset used for training"
    )
    trained_by: Optional[str] = Field(
        "Operator", description="User who started training job"
    )
    framework: Optional[str] = Field(
        "Ultralytics YOLOv8", description="ML library used"
    )
    commit_hash: Optional[str] = Field(
        None, description="Git commit hash of configuration repo"
    )
    model_size_mb: Optional[float] = Field(
        None, description="Model file size in megabytes"
    )
    parameter_count: Optional[int] = Field(None, description="Model parameter count")
    parent_version: Optional[str] = Field(
        None, description="Model checkpoint predecessor version"
    )
    notes: Optional[str] = Field(None, description="Training details and notes")


class ModelStatusUpdateRequest(BaseModel):
    version_name: str = Field(..., description="YOLO weights file name identifier")
    status: str = Field(
        ...,
        description="New lifecycle state: training | validated | staging | production | archived",
    )


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=ModelListResponse,
    summary="List versioned model weight files and metadata",
)
def list_available_models(db: Session = Depends(get_db)):
    """Retrieve list of all YOLOv8 checkpoints and metrics present in the registry database."""
    models = model_registry.get_models_from_db(db)
    return {"models": models}


@router.post(
    "/register",
    response_model=ModelVersionSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register new model checkpoint",
)
def register_model_checkpoint(req: ModelRegisterRequest, db: Session = Depends(get_db)):
    """Add a new model checkpoint version entry with rich evaluation metadata."""
    from app.core.repository import model_version_repo
    from app.models.db_models import ModelVersion

    existing = model_version_repo.get_by_version_name(db, req.version_name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model version '{req.version_name}' is already registered.",
        )

    new_ver = ModelVersion(
        version_name=req.version_name,
        file_path=req.file_path or str(model_registry.registry_dir / req.version_name),
        deployment_status=req.deployment_status,
        map_score=req.map_score,
        precision=req.precision,
        recall=req.recall,
        training_date=datetime.now(),
        dataset_name=req.dataset_name,
        trained_by=req.trained_by,
        framework=req.framework,
        commit_hash=req.commit_hash,
        artifact_path=req.file_path
        or str(model_registry.registry_dir / req.version_name),
        model_size_mb=req.model_size_mb,
        parameter_count=req.parameter_count,
        parent_version=req.parent_version,
        notes=req.notes,
    )

    # Save version
    model_version_repo.create(db, new_ver)
    return new_ver


@router.post("/switch", summary="Hot-swap active YOLOv8 weights and update status")
def switch_model_version(version_name: str, db: Session = Depends(get_db)):
    """Switch runtime YOLO weights dynamically to another version and promote to production status."""
    success = model_registry.promote_to_production(db, version_name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to switch to model version '{version_name}'. Verify file exists on server disk.",
        )
    return {
        "success": True,
        "detail": f"Active model successfully promoted and switched to {version_name}.",
    }


@router.post(
    "/status",
    response_model=ModelVersionSchema,
    summary="Update model deployment lifecycle state",
)
def update_model_status(req: ModelStatusUpdateRequest, db: Session = Depends(get_db)):
    """Update model status. Promoting to 'production' will automatically demote previous production version."""
    from app.core.repository import model_version_repo

    if req.status == "production":
        success = model_registry.promote_to_production(db, req.version_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to promote '{req.version_name}' to production weights.",
            )
        updated = model_version_repo.get_by_version_name(db, req.version_name)
    else:
        try:
            updated = model_version_repo.set_deployment_status(
                db, req.version_name, req.status
            )
        except ValueError as val_err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err)
            )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model version '{req.version_name}' not found.",
        )

    return updated
