"""
backend/app/core/events.py
──────────────────────────
Event Bus pattern for decoupled event publishing and subscribing (pub-sub).
"""

from typing import Callable, List, Dict
import asyncio
from app.core.logging import get_logger

logger = get_logger(__name__)

class EventBus:
    """Central event broker for Nika AI."""
    
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_name: str, handler: Callable) -> None:
        """Register a handler callback for a specific event."""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(handler)
        logger.debug(f"Subscribed handler '{handler.__name__}' to event '{event_name}'")

    def publish(self, event_name: str, payload: dict) -> None:
        """Publish an event to all registered subscriber callbacks asynchronously."""
        handlers = self._subscribers.get(event_name, [])
        if not handlers:
            return

        logger.info(f"Publishing event '{event_name}' to {len(handlers)} subscribers.")

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    # Use get_running_loop() — correct replacement for deprecated get_event_loop()
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(handler(payload))
                    except RuntimeError:
                        # No running event loop — skip async handler gracefully
                        logger.warning(
                            f"Cannot schedule async handler '{handler.__name__}': "
                            "no running event loop."
                        )
                else:
                    # Run synchronous handler in a daemon thread
                    import threading
                    threading.Thread(target=handler, args=(payload,), daemon=True).start()
            except Exception as exc:
                logger.error(f"Error executing event handler for '{event_name}': {exc}")

event_bus = EventBus()

# ── Register default handlers ──────────────────────────────────────────────────

def handle_prediction_finished_analytics(payload: dict):
    """Event handler to update live analytics when a prediction finishes."""
    logger.info("EventBus: Updating analytics snapshot for completed prediction.")

async def handle_prediction_finished_notifications(payload: dict):
    """Event handler to dispatch critical warnings if prediction contained defects.

    Runs detached from any request, so it opens and closes its own DB
    session rather than relying on the request-scoped `get_db` dependency.
    """
    status = payload.get("status")
    if status == "FAIL":
        from app.core.database import SessionLocal
        from app.services.notifications import NotificationService

        db = SessionLocal()
        try:
            await NotificationService.trigger_defect_alerts(
                db,
                defect_type=payload.get("defect_type", "Unknown"),
                confidence=payload.get("confidence", 0.0),
                machine_name=payload.get("machine_name", "Unknown"),
                machine_id=payload.get("machine_id"),
            )
        except Exception as exc:
            logger.error(f"EventBus Notification handler failed: {exc}")
        finally:
            db.close()

# Register listeners
event_bus.subscribe("prediction_finished", handle_prediction_finished_analytics)
event_bus.subscribe("prediction_finished", handle_prediction_finished_notifications)
