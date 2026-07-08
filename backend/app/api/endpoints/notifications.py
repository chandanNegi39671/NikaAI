"""
backend/app/api/endpoints/notifications.py
────────────────────────────────────────────
Notification history, filtering, and acknowledgement.

Dispatch itself happens via NotificationService (triggered by the event
bus or other services) — this module is read/ack surface only, so
operators can see what fired and clear it, not send arbitrary alerts.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import PermissionChecker, get_current_user
from app.core.database import get_db
from app.models.db_models import Notification, User
from app.services.notifications import NotificationService, VALID_CHANNELS, VALID_PRIORITIES

router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["Notifications"],
    dependencies=[Depends(PermissionChecker("analytics:read"))],
)


def _serialize(n: Notification) -> dict:
    return {
        "id": n.id,
        "event_type": n.event_type,
        "priority": n.priority,
        "title": n.title,
        "message": n.message,
        "machine_id": n.machine_id,
        "channel": n.channel,
        "recipient": n.recipient,
        "status": n.status,
        "attempts": n.attempts,
        "last_error": n.last_error,
        "sent_at": n.sent_at,
        "requires_ack": n.requires_ack,
        "acknowledged_at": n.acknowledged_at,
        "acknowledged_by": n.acknowledged_by,
        "escalated_at": n.escalated_at,
        "created_at": n.created_at,
    }


@router.get("")
def list_notifications(
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    machine_id: Optional[str] = Query(None),
    unacknowledged_only: bool = Query(False),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    """List notification history with filters, most recent first."""
    q = db.query(Notification).filter(Notification.is_deleted == False)

    if status_filter:
        q = q.filter(Notification.status == status_filter)
    if priority:
        if priority not in VALID_PRIORITIES:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"priority must be one of {VALID_PRIORITIES}")
        q = q.filter(Notification.priority == priority)
    if channel:
        if channel not in VALID_CHANNELS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"channel must be one of {VALID_CHANNELS}")
        q = q.filter(Notification.channel == channel)
    if machine_id:
        q = q.filter(Notification.machine_id == machine_id)
    if unacknowledged_only:
        q = q.filter(Notification.requires_ack == True, Notification.acknowledged_at.is_(None))

    total = q.count()
    items = q.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()
    return {"total": total, "limit": limit, "offset": offset, "items": [_serialize(n) for n in items]}


@router.get("/{notification_id}")
def get_notification(notification_id: str, db: Session = Depends(get_db)):
    """Fetch a single notification by id."""
    record = db.query(Notification).filter(
        Notification.id == notification_id, Notification.is_deleted == False
    ).first()
    if not record:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
    return _serialize(record)


@router.post("/{notification_id}/acknowledge", dependencies=[Depends(PermissionChecker("inspection:write"))])
def acknowledge_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Acknowledge a notification, halting further escalation."""
    record = NotificationService.acknowledge(db, notification_id, current_user.id)
    if not record:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
    return _serialize(record)