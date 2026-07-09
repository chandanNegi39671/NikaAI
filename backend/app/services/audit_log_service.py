"""
backend/app/services/audit_log_service.py
─────────────────────────────────────────
Audit Log query service for searching compliance logs.
"""

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.repository import audit_log_repo

logger = get_logger(__name__)


def list_audit_logs(
    db: Session,
    date_from: str | None = None,
    date_to: str | None = None,
    user_id: str | None = None,
    action: str | None = None,
    ip_address: str | None = None,
    entity_type: str | None = None,
    request_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Fetch paginated, filtered audit trail events from database repositories."""
    logger.info(f"Retrieving audit logs with offset={offset}, limit={limit}")

    results, total_count = audit_log_repo.list_with_filters(
        db,
        date_from=date_from,
        date_to=date_to,
        user_id=user_id,
        action=action,
        ip_address=ip_address,
        entity_type=entity_type,
        request_id=request_id,
        limit=limit,
        offset=offset,
    )

    formatted_results = []
    for log in results:
        formatted_results.append(
            {
                "id": log.id,
                "user_id": log.user_id,
                "username": log.user.username if log.user else None,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "description": log.description,
                "ip_address": log.ip_address,
                "old_value": log.old_value,
                "new_value": log.new_value,
                "request_id": log.request_id,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
        )

    return {
        "total": total_count,
        "results": formatted_results,
        "limit": limit,
        "offset": offset,
    }
