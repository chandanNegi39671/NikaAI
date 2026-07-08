"""
backend/app/core/middleware.py
──────────────────────────────
Global middleware for Nika AI.
"""

import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.perf_counter()

        # Generate or use existing Request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Process the request
        response = await call_next(request)

        # Calculate execution time
        process_time = time.perf_counter() - start_time

        # Add custom headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Use a relaxed CSP for Swagger/ReDoc doc pages so that unpkg.com
        # assets (JS, CSS) can load. All other routes get the strict policy.
        is_docs_path = request.url.path in ("/api/docs", "/api/redoc")

        if is_docs_path:
            csp = (
                "default-src 'self'; "
                "img-src 'self' data: blob: https://fastapi.tiangolo.com; "
                "style-src 'self' 'unsafe-inline' https://unpkg.com; "
                "script-src 'self' 'unsafe-inline' https://unpkg.com; "
                "connect-src 'self' https://unpkg.com; "
                "worker-src blob:; "
                "frame-ancestors 'none';"
            )
        else:
            csp = (
                "default-src 'self'; "
                "img-src 'self' data: blob:; "
                "style-src 'self' 'unsafe-inline'; "
                "script-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )

        response.headers["Content-Security-Policy"] = csp

        # Track HTTP request metrics and system performance metrics
        try:
            from app.core.metrics import REQUEST_COUNT, REQUEST_LATENCY, update_system_metrics
            method = request.method
            endpoint = request.url.path
            if endpoint != "/metrics":
                REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=response.status_code).inc()
                REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(process_time)
            update_system_metrics()
        except Exception:
            pass

        return response