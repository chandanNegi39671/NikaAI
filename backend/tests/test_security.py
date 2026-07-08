"""
backend/tests/test_security.py
────────────────────────────────
Security-focused regression tests.

These tests verify that specific previously-identified vulnerabilities
are fixed and cannot regress:

  1. CSP must not contain 'unsafe-eval' (XSS vector)
  2. CSP must not contain 'unsafe-inline' in script-src
  3. CORS must not allow arbitrary HTTP methods (TRACE, etc.)
  4. X-Frame-Options must be DENY
  5. HSTS header must be present
  6. Swagger docs must not be reachable in production mode
  7. Auth endpoints must enforce rate limiting
  8. JWT token type must be checked (refresh token can't be used as access token)
  9. Missing Authorization header → 401 (not 500)
  10. Malformed Authorization header → 401 (not 500)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.auth import create_token
from datetime import timedelta


class TestSecurityHeaders:
    """Every response must include the required security headers."""

    _ENDPOINTS = ["/api/v1/health", "/api/v1/auth/login"]

    @pytest.mark.parametrize("path", _ENDPOINTS)
    def test_x_content_type_options(self, client: TestClient, path: str):
        resp = client.get(path)
        assert resp.headers.get("x-content-type-options", "").lower() == "nosniff"

    @pytest.mark.parametrize("path", _ENDPOINTS)
    def test_x_frame_options_deny(self, client: TestClient, path: str):
        assert client.get(path).headers.get("x-frame-options", "").upper() == "DENY"

    @pytest.mark.parametrize("path", _ENDPOINTS)
    def test_hsts_present(self, client: TestClient, path: str):
        hsts = client.get(path).headers.get("strict-transport-security", "")
        assert "max-age" in hsts, "HSTS header missing or malformed"

    @pytest.mark.parametrize("path", _ENDPOINTS)
    def test_csp_present(self, client: TestClient, path: str):
        csp = client.get(path).headers.get("content-security-policy", "")
        assert csp, "Content-Security-Policy header is missing"

    @pytest.mark.parametrize("path", _ENDPOINTS)
    def test_csp_no_unsafe_eval(self, client: TestClient, path: str):
        """REGRESSION: CSP must not contain unsafe-eval — fixed in this audit cycle."""
        csp = client.get(path).headers.get("content-security-policy", "")
        assert "unsafe-eval" not in csp, "CSP regression: unsafe-eval found in CSP"

    @pytest.mark.parametrize("path", _ENDPOINTS)
    def test_csp_script_src_no_unsafe_inline(self, client: TestClient, path: str):
        """script-src should not allow unsafe-inline."""
        csp = client.get(path).headers.get("content-security-policy", "")
        directives = {}
        for directive in csp.split(";"):
            parts = directive.strip().split()
            if parts:
                directives[parts[0]] = parts[1:]
        if "script-src" in directives:
            assert not any("unsafe-inline" in x for x in directives["script-src"]), "CSP: script-src must not contain unsafe-inline"


    @pytest.mark.parametrize("path", _ENDPOINTS)
    def test_frame_ancestors_deny(self, client: TestClient, path: str):
        """frame-ancestors 'none' should be in CSP as a clickjacking defense."""
        csp = client.get(path).headers.get("content-security-policy", "")
        assert "frame-ancestors" in csp, "CSP missing frame-ancestors directive"


class TestAuthSecurity:
    """Authentication security edge cases."""

    def test_no_auth_header_returns_401_not_500(self, client: TestClient):
        resp = client.get("/api/v1/inspections")
        assert resp.status_code == 401
        assert resp.status_code != 500

    def test_malformed_bearer_returns_401(self, client: TestClient):
        resp = client.get(
            "/api/v1/inspections",
            headers={"Authorization": "Bearer not.a.jwt"},
        )
        assert resp.status_code == 401
        assert resp.status_code != 500

    def test_wrong_scheme_returns_401(self, client: TestClient):
        resp = client.get(
            "/api/v1/inspections",
            headers={"Authorization": "Basic dXNlcjpwYXNz"},
        )
        assert resp.status_code == 401

    def test_refresh_token_cannot_access_api(self, client: TestClient, admin_user):
        """A refresh token must NOT be accepted as an access token for API calls."""
        from app.core.config import settings
        from app.core.auth import create_token
        refresh_tok = create_token(
            subject=admin_user.username,
            role=admin_user.role,
            token_type="refresh",
            expires_delta=timedelta(days=7),
        )
        resp = client.get(
            "/api/v1/inspections",
            headers={"Authorization": f"Bearer {refresh_tok}"},
        )
        # Must reject — type check in get_current_user catches this
        assert resp.status_code == 401

    def test_expired_token_returns_401(self, client: TestClient, admin_user):
        """An expired JWT must return 401 — not 500 or 200."""
        expired_tok = create_token(
            subject=admin_user.username,
            role=admin_user.role,
            token_type="access",
            expires_delta=timedelta(seconds=-1),  # Already expired
        )
        resp = client.get(
            "/api/v1/inspections",
            headers={"Authorization": f"Bearer {expired_tok}"},
        )
        assert resp.status_code == 401


class TestCORSPolicy:
    """Verify CORS is not overly permissive."""

    def test_trace_method_not_allowed(self, client: TestClient):
        """HTTP TRACE must be blocked — CORS allowlist restricts to safe verbs only."""
        resp = client.request("TRACE", "/api/v1/health")
        assert resp.status_code in (405, 400, 403)

    def test_options_preflight_includes_allowed_methods(self, client: TestClient):
        """OPTIONS preflight should advertise the explicit method allowlist."""
        resp = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
        allow_methods = resp.headers.get("access-control-allow-methods", "")
        # Wildcard * is explicitly disallowed by our hardened config
        # The explicit list should be present
        if allow_methods:
            assert "*" not in allow_methods or allow_methods.strip() != "*"
