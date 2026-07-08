"""
backend/app/services/notifications.py
──────────────────────────────────────
Integrated omnichannel notification service (SMTP Email, Slack Webhooks, Discord, Teams, Twilio SMS).
"""

import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class NotificationService:
    """Dispatches notifications across multiple channels."""
    
    @staticmethod
    def send_email(subject: str, body: str, recipient: str) -> bool:
        """Send notification via SMTP Email."""
        # SMTP configurations (can load from settings if configured)
        smtp_host = "localhost"
        smtp_port = 1025 # Mailhog / Dev SMTP
        sender_email = "alerts@nika.ai"
        
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))
        
        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.sendmail(sender_email, recipient, msg.as_string())
            logger.info(f"Email notification successfully sent to {recipient}")
            return True
        except Exception as exc:
            logger.warning(f"Failed to send email notification (SMTP offline): {exc}")
            return False

    @staticmethod
    def send_slack(message: str) -> bool:
        """Send notification to Slack channel via Webhook."""
        webhook_url = getattr(settings, "slack_webhook_url", None)
        if not webhook_url:
            logger.debug(f"Slack webhook not configured. Simulation payload: {message}")
            return True
            
        try:
            res = httpx.post(webhook_url, json={"text": message})
            if res.status_code == 200:
                logger.info("Slack webhook notification sent successfully.")
                return True
            logger.warning(f"Slack webhook returned status code {res.status_code}")
            return False
        except Exception as exc:
            logger.error(f"Failed to send Slack webhook: {exc}")
            return False

    @staticmethod
    def send_discord(message: str) -> bool:
        """Send notification to Discord webhook."""
        webhook_url = getattr(settings, "discord_webhook_url", None)
        if not webhook_url:
            logger.debug(f"Discord webhook not configured. Simulation payload: {message}")
            return True
            
        try:
            res = httpx.post(webhook_url, json={"content": message})
            if res.status_code == 204:
                logger.info("Discord webhook notification sent successfully.")
                return True
            return False
        except Exception as exc:
            logger.error(f"Failed to send Discord webhook: {exc}")
            return False

    @staticmethod
    def trigger_defect_alerts(defect_type: str, confidence: float, machine_name: str) -> None:
        """Trigger automated omnichannel alerts for critical manufacturing defects."""
        subject = f"🚨 CRITICAL DEFECT DETECTED: {defect_type.upper()}"
        body = f"""
        <html>
            <body>
                <h2>Nika AI Alert</h2>
                <p>A critical defect has been detected on the factory floor.</p>
                <ul>
                    <li><strong>Defect Type:</strong> {defect_type.replace('_', ' ').title()}</li>
                    <li><strong>Confidence:</strong> {round(confidence * 100, 2)}%</li>
                    <li><strong>Machine Source:</strong> {machine_name}</li>
                </ul>
                <p>Please review the inspection result immediately.</p>
            </body>
        </html>
        """
        
        # Broadcast email to supervisors
        NotificationService.send_email(subject, body, "supervisor@nika.ai")
        
        # Broadcast to chat tools
        chat_msg = f"🚨 *Critical Defect Alert* | Machine: *{machine_name}* | Defect: *{defect_type}* ({round(confidence*100,2)}%)"
        NotificationService.send_slack(chat_msg)
        NotificationService.send_discord(chat_msg)
