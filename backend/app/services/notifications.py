"""
backend/app/services/notifications.py
──────────────────────────────────────
Multi-channel notification dispatch: email, Slack, Microsoft Teams,
Discord, SMS (Twilio), and generic outbound webhooks.

Design choices worth calling out:
  - Every dispatch attempt is persisted as a `Notification` row *before*
    delivery is attempted, so a crash mid-send still leaves an audit
    trail instead of losing the event entirely.
  - A channel with no credentials configured is skipped and recorded as
    `status="failed"` with a clear reason — it never reports fake
    success just because nothing was configured.
  - Delivery is async (httpx.AsyncClient) so a slow/unreachable webhook
    can't block the event loop or an inference request.
  - `escalate_unacknowledged` is a separate, idempotent operation meant
    to be called periodically (e.g. from a Celery beat task) rather than
    inline during dispatch, since escalation is a time-based condition.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.db_models import Notification

logger = get_logger(__name__)

VALID_PRIORITIES = {"low", "normal", "high", "critical"}
VALID_CHANNELS = {"email", "slack", "teams", "discord", "sms", "webhook"}


class ChannelNotConfigured(Exception):
    """Raised internally when a channel is requested but has no credentials."""


class NotificationService:
    """Dispatches notifications across multiple channels and persists results."""

    # ── Per-channel senders ──────────────────────────────────────────────
    # Each returns nothing; raises on failure so the caller can record the
    # real error message rather than a generic "failed".

    @staticmethod
    async def _send_email(subject: str, body_html: str, recipient: str) -> None:
        if not settings.smtp_host:
            raise ChannelNotConfigured("SMTP_HOST is not configured")

        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        import aiosmtplib

        msg = MIMEMultipart()
        msg["From"] = settings.smtp_from_address
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body_html, "html"))

        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            start_tls=settings.smtp_use_tls,
        )

    @staticmethod
    async def _send_slack(message: str) -> None:
        if not settings.slack_webhook_url:
            raise ChannelNotConfigured("SLACK_WEBHOOK_URL is not configured")
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(settings.slack_webhook_url, json={"text": message})
            res.raise_for_status()

    @staticmethod
    async def _send_teams(title: str, message: str) -> None:
        if not settings.teams_webhook_url:
            raise ChannelNotConfigured("TEAMS_WEBHOOK_URL is not configured")
        # Teams incoming webhooks expect an Adaptive Card / MessageCard payload,
        # not a plain "text" field like Slack/Discord.
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "summary": title,
            "themeColor": "D0021B",
            "title": title,
            "text": message,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(settings.teams_webhook_url, json=payload)
            res.raise_for_status()

    @staticmethod
    async def _send_discord(message: str) -> None:
        if not settings.discord_webhook_url:
            raise ChannelNotConfigured("DISCORD_WEBHOOK_URL is not configured")
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                settings.discord_webhook_url, json={"content": message}
            )
            res.raise_for_status()

    @staticmethod
    async def _send_sms(message: str, to_number: str) -> None:
        if not (
            settings.twilio_account_sid
            and settings.twilio_auth_token
            and settings.twilio_from_number
        ):
            raise ChannelNotConfigured("Twilio credentials are not fully configured")
        url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                url,
                data={
                    "From": settings.twilio_from_number,
                    "To": to_number,
                    "Body": message,
                },
                auth=(settings.twilio_account_sid, settings.twilio_auth_token),
            )
            res.raise_for_status()

    @staticmethod
    async def _send_webhook(url: str, payload: dict[str, Any]) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(url, json=payload)
            res.raise_for_status()

    # ── Orchestration ────────────────────────────────────────────────────

    @staticmethod
    async def dispatch(
        db: Session,
        *,
        event_type: str,
        title: str,
        message: str,
        channels: list[str],
        priority: str = "normal",
        machine_id: str | None = None,
        recipients: dict[str, str] | None = None,
        webhook_url: str | None = None,
        requires_ack: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> list[Notification]:
        """Persist and attempt delivery of one notification across N channels.

        `recipients` maps channel -> address, e.g. {"email": "sup@nika.ai", "sms": "+1..."}.
        Returns the list of persisted Notification rows (one per channel),
        each reflecting its real delivery outcome.
        """
        if priority not in VALID_PRIORITIES:
            raise ValueError(
                f"priority must be one of {VALID_PRIORITIES}, got '{priority}'"
            )
        unknown = set(channels) - VALID_CHANNELS
        if unknown:
            raise ValueError(f"unknown channel(s): {unknown}")

        recipients = recipients or {}
        results: list[Notification] = []

        for channel in channels:
            record = Notification(
                event_type=event_type,
                priority=priority,
                title=title,
                message=message,
                machine_id=machine_id,
                metadata_json=json.dumps(metadata) if metadata else None,
                channel=channel,
                recipient=recipients.get(channel),
                status="pending",
                attempts=0,
                requires_ack=requires_ack,
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            for attempt in range(1, settings.notification_max_retries + 1):
                record.attempts = attempt
                try:
                    if channel == "email":
                        await NotificationService._send_email(
                            title,
                            message,
                            recipients.get("email", settings.smtp_from_address),
                        )
                    elif channel == "slack":
                        await NotificationService._send_slack(f"*{title}*\n{message}")
                    elif channel == "teams":
                        await NotificationService._send_teams(title, message)
                    elif channel == "discord":
                        await NotificationService._send_discord(
                            f"**{title}**\n{message}"
                        )
                    elif channel == "sms":
                        to_number = recipients.get("sms")
                        if not to_number:
                            raise ChannelNotConfigured(
                                "no SMS recipient number provided"
                            )
                        await NotificationService._send_sms(
                            f"{title}: {message}", to_number
                        )
                    elif channel == "webhook":
                        if not webhook_url:
                            raise ChannelNotConfigured("no webhook_url provided")
                        await NotificationService._send_webhook(
                            webhook_url,
                            {
                                "event_type": event_type,
                                "title": title,
                                "message": message,
                                "priority": priority,
                                "machine_id": machine_id,
                                "metadata": metadata,
                            },
                        )

                    record.status = "sent"
                    record.sent_at = datetime.now(timezone.utc)
                    record.last_error = None
                    break

                except ChannelNotConfigured as exc:
                    # Not configured is not worth retrying.
                    record.status = "failed"
                    record.last_error = str(exc)
                    logger.debug(f"Notification channel '{channel}' skipped: {exc}")
                    break

                except Exception as exc:
                    record.last_error = str(exc)
                    logger.warning(
                        f"Notification via '{channel}' failed (attempt {attempt}): {exc}"
                    )
                    if attempt == settings.notification_max_retries:
                        record.status = "failed"

            db.commit()
            db.refresh(record)
            results.append(record)

        return results

    @staticmethod
    def acknowledge(
        db: Session, notification_id: str, user_id: str
    ) -> Notification | None:
        """Mark a notification acknowledged, stopping further escalation."""
        record = (
            db.query(Notification)
            .filter(
                Notification.id == notification_id, Notification.is_deleted == False
            )
            .first()
        )
        if not record:
            return None
        record.acknowledged_at = datetime.now(timezone.utc)
        record.acknowledged_by = user_id
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_unacknowledged_for_escalation(db: Session) -> list[Notification]:
        """Find critical/high-priority notifications past the escalation
        window that are still unacknowledged and haven't already escalated."""
        cutoff = datetime.now(timezone.utc) - timedelta(
            minutes=settings.notification_escalation_minutes
        )
        return (
            db.query(Notification)
            .filter(
                Notification.is_deleted == False,
                Notification.requires_ack == True,
                Notification.acknowledged_at.is_(None),
                Notification.escalated_at.is_(None),
                Notification.priority.in_(["high", "critical"]),
                Notification.created_at <= cutoff,
            )
            .all()
        )

    @staticmethod
    async def escalate_unacknowledged(db: Session) -> int:
        """Re-broadcast unacknowledged critical/high alerts to email + Slack
        as an escalation, and stamp them so they don't escalate repeatedly.
        Intended to be run periodically (e.g. Celery beat). Returns count escalated.
        """
        pending = NotificationService.get_unacknowledged_for_escalation(db)
        for record in pending:
            escalation_msg = (
                f"⚠️ ESCALATION: '{record.title}' has been unacknowledged for over "
                f"{settings.notification_escalation_minutes} minutes."
            )
            await NotificationService.dispatch(
                db,
                event_type=f"{record.event_type}_escalation",
                title=f"[ESCALATED] {record.title}",
                message=escalation_msg,
                channels=["email", "slack"],
                priority="critical",
                machine_id=record.machine_id,
                requires_ack=False,
            )
            record.escalated_at = datetime.now(timezone.utc)
        db.commit()
        return len(pending)

    @staticmethod
    async def trigger_defect_alerts(
        db: Session,
        defect_type: str,
        confidence: float,
        machine_name: str,
        machine_id: str | None = None,
    ) -> list[Notification]:
        """Convenience wrapper for the most common alert: a critical defect detection."""
        title = f"🚨 Critical defect detected: {defect_type.replace('_', ' ').title()}"
        message = (
            f"A critical defect has been detected on the factory floor.\n"
            f"Defect type: {defect_type.replace('_', ' ').title()}\n"
            f"Confidence: {round(confidence * 100, 2)}%\n"
            f"Machine: {machine_name}\n"
            f"Please review the inspection result immediately."
        )
        return await NotificationService.dispatch(
            db,
            event_type="critical_defect",
            title=title,
            message=message,
            channels=["email", "slack", "discord"],
            priority="critical",
            machine_id=machine_id,
            recipients={"email": "supervisor@nika.ai"},
            requires_ack=True,
            metadata={
                "defect_type": defect_type,
                "confidence": confidence,
                "machine_name": machine_name,
            },
        )
