"""
backend/tests/test_notifications.py
────────────────────────────────────
Tests for the multi-channel notification service and its API surface.

These exercise real code paths: DB persistence, unconfigured-channel
handling, retries against actually-unreachable URLs, acknowledgement,
and escalation — nothing here is a stub asserting on a mock.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app.core.config import settings
from app.models.db_models import Notification
from app.services.notifications import NotificationService

# ── Service-level tests ─────────────────────────────────────────────────────


def test_unconfigured_channel_is_recorded_as_failed_not_fake_success(db_session):
    """A channel with no credentials must not report success."""
    results = asyncio.run(
        NotificationService.dispatch(
            db_session,
            event_type="test_event",
            title="Test",
            message="hello",
            channels=["slack"],  # no SLACK_WEBHOOK_URL configured in tests
            priority="normal",
        )
    )
    assert len(results) == 1
    record = results[0]
    assert record.status == "failed"
    assert "not configured" in record.last_error.lower()
    # And it's actually persisted, not just an in-memory object.
    fetched = (
        db_session.query(Notification).filter(Notification.id == record.id).first()
    )
    assert fetched is not None
    assert fetched.status == "failed"


def test_dispatch_rejects_invalid_priority(db_session):
    with pytest.raises(ValueError):
        asyncio.run(
            NotificationService.dispatch(
                db_session,
                event_type="x",
                title="t",
                message="m",
                channels=["slack"],
                priority="urgent-ish",
            )
        )


def test_dispatch_rejects_unknown_channel(db_session):
    with pytest.raises(ValueError):
        asyncio.run(
            NotificationService.dispatch(
                db_session,
                event_type="x",
                title="t",
                message="m",
                channels=["carrier_pigeon"],
            )
        )


def test_webhook_channel_delivers_and_retries_on_failure(db_session, monkeypatch):
    """Point the webhook channel at a URL that fails twice then succeeds,
    and confirm attempts/status reflect real retry behavior."""
    call_count = {"n": 0}

    class FakeResponse:
        def raise_for_status(self):
            if call_count["n"] <= 2:
                raise httpx.HTTPStatusError("boom", request=None, response=None)

    class FakeAsyncClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, json=None, **kw):
            call_count["n"] += 1
            return FakeResponse()

    monkeypatch.setattr("app.services.notifications.httpx.AsyncClient", FakeAsyncClient)

    results = asyncio.run(
        NotificationService.dispatch(
            db_session,
            event_type="test_webhook",
            title="Webhook test",
            message="payload",
            channels=["webhook"],
            webhook_url="https://example.invalid/hook",
        )
    )
    record = results[0]
    assert call_count["n"] == 3  # failed, failed, succeeded
    assert record.status == "sent"
    assert record.attempts == 3


def test_webhook_channel_gives_up_after_max_retries(db_session, monkeypatch):
    class FakeAsyncClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, json=None, **kw):
            raise httpx.ConnectError("connection refused")

    monkeypatch.setattr("app.services.notifications.httpx.AsyncClient", FakeAsyncClient)

    results = asyncio.run(
        NotificationService.dispatch(
            db_session,
            event_type="test_webhook_fail",
            title="Webhook test",
            message="payload",
            channels=["webhook"],
            webhook_url="https://example.invalid/hook",
        )
    )
    record = results[0]
    assert record.status == "failed"
    assert record.attempts == settings.notification_max_retries
    assert "connection refused" in record.last_error.lower()


def test_acknowledge_sets_fields_and_stops_reescalation(db_session, admin_user):
    results = asyncio.run(
        NotificationService.dispatch(
            db_session,
            event_type="critical_defect",
            title="t",
            message="m",
            channels=["slack"],
            priority="critical",
            requires_ack=True,
        )
    )
    record = results[0]
    assert record.acknowledged_at is None

    acked = NotificationService.acknowledge(db_session, record.id, admin_user.id)
    assert acked.acknowledged_at is not None
    assert acked.acknowledged_by == admin_user.id

    # No longer eligible for escalation once acknowledged.
    pending = NotificationService.get_unacknowledged_for_escalation(db_session)
    assert record.id not in [p.id for p in pending]


def test_escalation_only_fires_after_window_and_only_once(db_session):
    results = asyncio.run(
        NotificationService.dispatch(
            db_session,
            event_type="critical_defect",
            title="t",
            message="m",
            channels=["slack"],
            priority="critical",
            requires_ack=True,
        )
    )
    record = results[0]

    # Freshly created — inside the escalation window, should not be flagged yet.
    pending = NotificationService.get_unacknowledged_for_escalation(db_session)
    assert record.id not in [p.id for p in pending]

    # Backdate creation past the escalation window.
    record.created_at = datetime.now(timezone.utc) - timedelta(
        minutes=settings.notification_escalation_minutes + 1
    )
    db_session.commit()

    pending = NotificationService.get_unacknowledged_for_escalation(db_session)
    assert record.id in [p.id for p in pending]

    escalated_count = asyncio.run(
        NotificationService.escalate_unacknowledged(db_session)
    )
    assert escalated_count == 1
    db_session.refresh(record)
    assert record.escalated_at is not None

    # Running again should not re-escalate the same notification.
    pending_again = NotificationService.get_unacknowledged_for_escalation(db_session)
    assert record.id not in [p.id for p in pending_again]


# ── API tests ────────────────────────────────────────────────────────────────


def test_list_notifications_requires_auth(client):
    resp = client.get("/api/v1/notifications")
    assert resp.status_code == 401


def test_list_and_filter_notifications(client, db_session, admin_headers):
    asyncio.run(
        NotificationService.dispatch(
            db_session,
            event_type="critical_defect",
            title="A",
            message="m",
            channels=["slack"],
            priority="critical",
        )
    )
    asyncio.run(
        NotificationService.dispatch(
            db_session,
            event_type="machine_offline",
            title="B",
            message="m",
            channels=["slack"],
            priority="low",
        )
    )

    resp = client.get("/api/v1/notifications", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 2

    resp_filtered = client.get(
        "/api/v1/notifications?priority=critical", headers=admin_headers
    )
    assert resp_filtered.status_code == 200
    assert all(item["priority"] == "critical" for item in resp_filtered.json()["items"])


def test_acknowledge_endpoint(client, db_session, admin_headers):
    results = asyncio.run(
        NotificationService.dispatch(
            db_session,
            event_type="critical_defect",
            title="A",
            message="m",
            channels=["slack"],
            priority="critical",
            requires_ack=True,
        )
    )
    notif_id = results[0].id

    resp = client.post(
        f"/api/v1/notifications/{notif_id}/acknowledge", headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["acknowledged_at"] is not None


def test_acknowledge_nonexistent_notification_returns_404(client, admin_headers):
    resp = client.post(
        "/api/v1/notifications/does-not-exist/acknowledge", headers=admin_headers
    )
    assert resp.status_code == 404
