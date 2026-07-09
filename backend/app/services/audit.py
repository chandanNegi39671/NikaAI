"""
backend/app/services/audit.py
─────────────────────────────
Audit log helper service to record user activity and changes.
"""

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.db_models import AuditLog

logger = get_logger(__name__)


def log_activity(
    db: Session,
    action: str,
    user_id: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    description: str | None = None,
    request: Request | None = None,
) -> AuditLog | None:
    """Create a database audit log entry for compliance tracking."""
    try:
        ip_address = None
        user_agent = None

        if request:
            # Try to fetch real IP address from proxies
            ip_address = request.headers.get(
                "X-Forwarded-For", request.client.host if request.client else None
            )
            user_agent = request.headers.get("User-Agent")

        full_desc = description or ""
        if user_agent:
            full_desc = f"{full_desc} [UA: {user_agent}]".strip()

        audit = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=full_desc,
            ip_address=ip_address,
        )
        db.add(audit)
        db.commit()
        db.refresh(audit)

        logger.info(f"Audit log created: Action={action}, User={user_id}")
        return audit
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to write audit log: {exc}")
        return None
