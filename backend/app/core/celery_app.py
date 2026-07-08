"""
backend/app/core/celery_app.py
──────────────────────────────
Celery application configuration for background asynchronous task execution.
"""

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "nika_ai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Automatically register tasks in services
celery_app.autodiscover_tasks(["app.services.tasks"])

# ── Celery Beat Scheduler Configuration ───────────────────────────────────────
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "generate-daily-report": {
        "task": "app.services.tasks.generate_scheduled_report",
        "schedule": crontab(hour=0, minute=0),
        "args": ("daily",)
    },
    "generate-weekly-report": {
        "task": "app.services.tasks.generate_scheduled_report",
        "schedule": crontab(day_of_week="sun", hour=0, minute=0),
        "args": ("weekly",)
    },
    "generate-monthly-report": {
        "task": "app.services.tasks.generate_scheduled_report",
        "schedule": crontab(day_of_month=1, hour=0, minute=0),
        "args": ("monthly",)
    },
    "nika-system-backup": {
        "task": "app.services.tasks.run_system_backup",
        "schedule": crontab(day_of_week="sun", hour=2, minute=0)
    }
}
