"""
backend/app/api/endpoints/audit_logs.py
───────────────────────────────────────
Endpoints for querying and filtering compliance audit trail events.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_db
from app.services.audit_log_service import list_audit_logs
from app.core.auth import PermissionChecker

router = APIRouter(
    prefix="/api/v1/audit",
    tags=["Compliance Audit"],
    dependencies=[Depends(PermissionChecker("analytics:read"))] # Admin / Supervisor roles
)

# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class AuditLogItemSchema(BaseModel):
    id: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    request_id: Optional[str] = None
    created_at: Optional[str] = None

class AuditLogsResponse(BaseModel):
    total: int
    results: List[AuditLogItemSchema]
    limit: int
    offset: int


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("", response_model=AuditLogsResponse, summary="Query compliance logs")
def query_audit_logs(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    ip_address: Optional[str] = None,
    entity_type: Optional[str] = None,
    request_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Retrieve compliance operations log items. Access is restricted to Supervisor / Admin roles."""
    logs = list_audit_logs(
        db,
        date_from=date_from,
        date_to=date_to,
        user_id=user_id,
        action=action,
        ip_address=ip_address,
        entity_type=entity_type,
        request_id=request_id,
        limit=limit,
        offset=offset
    )
    return logs
