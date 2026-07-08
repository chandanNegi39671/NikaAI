"""
backend/app/core/telemetry.py
──────────────────────────────
OpenTelemetry Distributed Tracing setup for Nika AI.

Imports are deferred inside setup_telemetry() so that missing optional
packages (opentelemetry-sdk, instrumentation libs) do not crash app
startup. The application degrades gracefully — tracing is simply skipped
and a warning is logged.
"""

from app.core.logging import get_logger

logger = get_logger(__name__)


def setup_telemetry(app) -> None:
    """Initialize OpenTelemetry Distributed Tracing (optional, graceful fallback)."""
    try:
        # Lazy imports — only attempted at call time, not at module import time.
        # This prevents a ModuleNotFoundError from crashing the entire app when
        # the opentelemetry-sdk package is not installed.
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        # Set up a tracer provider
        provider = TracerProvider()

        # Output trace spans to stdout/console for dev observability
        processor = BatchSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(processor)

        # Register global tracer provider
        trace.set_tracer_provider(provider)

        # Instrument FastAPI app
        FastAPIInstrumentor.instrument_app(app)

        # Instrument SQLAlchemy queries
        from app.core.database import engine
        SQLAlchemyInstrumentor().instrument(engine=engine)

        logger.info("OpenTelemetry distributed tracing configured successfully.")

    except ImportError as exc:
        logger.warning(
            f"OpenTelemetry packages not installed — tracing disabled. "
            f"Install opentelemetry-sdk and instrumentation packages to enable. ({exc})"
        )
    except Exception as exc:
        logger.warning(f"Could not configure OpenTelemetry distributed tracing: {exc}")
