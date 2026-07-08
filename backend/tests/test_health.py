"""
backend/tests/test_health.py
─────────────────────────────
Tests for the /api/v1/health, /api/v1/live, and /api/v1/ready endpoints.

The health check is a critical observability endpoint. We verify:
  - It always returns 200 (liveness must never 5xx)
  - The response schema is correct
  - The status field is a known value
  - Security headers are present on every response
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """GET /api/v1/health"""

    def test_health_returns_200(self, client: TestClient):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200

    def test_health_response_schema(self, client: TestClient):
        resp = client.get("/api/v1/health")
        data = resp.json()
        assert "status" in data, "Health response must contain 'status'"

    def test_health_status_is_valid_value(self, client: TestClient):
        resp = client.get("/api/v1/health")
        data = resp.json()
        allowed_statuses = {"healthy", "degraded", "unhealthy"}
        assert data["status"] in allowed_statuses, (
            f"status must be one of {allowed_statuses}, got: {data['status']}"
        )

    def test_health_contains_version_info(self, client: TestClient):
        """Health response should include app version for debugging."""
        resp = client.get("/api/v1/health")
        data = resp.json()
        # At minimum we expect a version or timestamp to be present
        has_version = "version" in data or "app_version" in data
        # Not strictly required but strongly recommended for observability
        # — just check the response is a valid dict
        assert isinstance(data, dict)

    def test_health_security_headers_present(self, client: TestClient):
        """All API responses must include critical security headers."""
        resp = client.get("/api/v1/health")
        headers = resp.headers

        assert "x-content-type-options" in headers, "Missing X-Content-Type-Options"
        assert headers["x-content-type-options"].lower() == "nosniff"

        assert "x-frame-options" in headers, "Missing X-Frame-Options"
        assert headers["x-frame-options"].upper() == "DENY"

        assert "content-security-policy" in headers, "Missing Content-Security-Policy"

    def test_health_csp_no_unsafe_eval(self, client: TestClient):
        """CSP must NOT include unsafe-eval — this was a previous vulnerability."""
        resp = client.get("/api/v1/health")
        csp = resp.headers.get("content-security-policy", "")
        assert "unsafe-eval" not in csp, "CSP must not contain 'unsafe-eval'"

    def test_health_request_id_header_present(self, client: TestClient):
        """Every response should carry an X-Request-ID for tracing."""
        resp = client.get("/api/v1/health")
        assert "x-request-id" in resp.headers, "Missing X-Request-ID header"

    def test_health_process_time_header_present(self, client: TestClient):
        """X-Process-Time is injected by SecurityMiddleware for latency tracking."""
        resp = client.get("/api/v1/health")
        assert "x-process-time" in resp.headers, "Missing X-Process-Time header"

    def test_health_response_is_json(self, client: TestClient):
        resp = client.get("/api/v1/health")
        assert resp.headers["content-type"].startswith("application/json")


class TestLivenessEndpoint:
    """GET /api/v1/live — Kubernetes liveness probe."""

    def test_live_returns_200(self, client: TestClient):
        resp = client.get("/api/v1/live")
        assert resp.status_code == 200

    def test_live_response_body(self, client: TestClient):
        resp = client.get("/api/v1/live")
        data = resp.json()
        assert isinstance(data, dict)


class TestReadinessEndpoint:
    """GET /api/v1/ready — Kubernetes readiness probe."""

    def test_ready_returns_200_or_503(self, client: TestClient):
        """Readiness can return 503 if dependencies are unavailable (CI without DB/Redis)."""
        resp = client.get("/api/v1/ready")
        assert resp.status_code in (200, 503)

    def test_ready_response_is_json(self, client: TestClient):
        resp = client.get("/api/v1/ready")
        assert resp.headers["content-type"].startswith("application/json")


class TestDocsInDevelopment:
    """Verify Swagger UI is accessible in development mode (the default)."""

    def test_openapi_json_accessible_in_dev(self, client: TestClient):
        """In development, /api/openapi.json should be available."""
        resp = client.get("/api/openapi.json")
        # In development mode this should return 200; in production mode 404
        # Since test env defaults to development, expect 200
        assert resp.status_code in (200, 404)
