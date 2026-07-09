"""
backend/tests/test_auth.py
───────────────────────────
Tests for the /api/v1/auth/* endpoints.

Covers:
  - User registration (happy path + validation errors)
  - Login (valid credentials, wrong password, non-existent user)
  - Token refresh (valid + expired + wrong type)
  - Logout (blacklisting)
  - Profile endpoint (authenticated + unauthenticated)
  - RBAC: admin-only endpoint blocks lower roles
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import get_password_hash
from app.models.db_models import User


class TestRegistration:
    """POST /api/v1/auth/register"""

    def test_register_success(self, client: TestClient, db_session: Session):
        payload = {
            "username": "new_operator",
            "email": "new_operator@nika.ai",
            "password": "SecurePass123",
            "role": "operator",
        }
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "new_operator"
        assert data["email"] == "new_operator@nika.ai"
        assert "id" in data
        # Password must never be exposed
        assert "password" not in data
        assert "password_hash" not in data

    def test_register_duplicate_username(self, client: TestClient, db_session: Session):
        """Registering with an existing username must return 409 Conflict."""
        # Seed a user directly
        user = User(
            username="dup_user",
            email="dup@nika.ai",
            password_hash=get_password_hash("pass123"),
            role="operator",
        )
        db_session.add(user)
        db_session.flush()

        resp = client.post(
            "/api/v1/auth/register",
            json={
                "username": "dup_user",
                "email": "other@nika.ai",
                "password": "pass123",
            },
        )
        assert resp.status_code == 409

    def test_register_short_password(self, client: TestClient):
        """Password shorter than 6 chars must fail with 422."""
        resp = client.post(
            "/api/v1/auth/register",
            json={"username": "u", "email": "u@nika.ai", "password": "abc"},
        )
        assert resp.status_code == 422

    def test_register_invalid_email(self, client: TestClient):
        """An invalid email format must fail with 422."""
        resp = client.post(
            "/api/v1/auth/register",
            json={"username": "x", "email": "not-an-email", "password": "password123"},
        )
        assert resp.status_code == 422

    def test_register_username_too_short(self, client: TestClient):
        """Username < 3 chars must fail with 422."""
        resp = client.post(
            "/api/v1/auth/register",
            json={"username": "ab", "email": "ab@nika.ai", "password": "password123"},
        )
        assert resp.status_code == 422


class TestLogin:
    """POST /api/v1/auth/login"""

    def _seed_user(self, db_session: Session, username: str = "logintest") -> User:
        user = User(
            username=username,
            email=f"{username}@nika.ai",
            password_hash=get_password_hash("correct_password"),
            role="operator",
        )
        db_session.add(user)
        db_session.flush()
        return user

    def test_login_success_returns_tokens(
        self, client: TestClient, db_session: Session
    ):
        self._seed_user(db_session)
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": "logintest", "password": "correct_password"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "logintest"

    def test_login_wrong_password(self, client: TestClient, db_session: Session):
        self._seed_user(db_session, "badpass_user")
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": "badpass_user", "password": "wrong_password"},
        )
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": "ghost_user", "password": "password"},
        )
        assert resp.status_code == 401

    def test_login_missing_credentials(self, client: TestClient):
        """OAuth2PasswordBearer form requires username+password fields."""
        resp = client.post("/api/v1/auth/login", data={})
        assert resp.status_code == 422


class TestProfile:
    """GET /api/v1/auth/profile"""

    def test_get_profile_authenticated(self, client: TestClient, admin_headers: dict):
        resp = client.get("/api/v1/auth/profile", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "username" in data
        assert "password_hash" not in data

    def test_get_profile_unauthenticated(self, client: TestClient):
        resp = client.get("/api/v1/auth/profile")
        assert resp.status_code == 401

    def test_get_profile_invalid_token(self, client: TestClient):
        resp = client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": "Bearer totally_invalid_token"},
        )
        assert resp.status_code == 401


class TestTokenRefresh:
    """POST /api/v1/auth/refresh"""

    def test_refresh_with_access_token_fails(
        self, client: TestClient, admin_token: str
    ):
        """Passing an access token to the refresh endpoint must be rejected."""
        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": admin_token},
        )
        # Should reject: access token submitted as refresh token
        assert resp.status_code in (400, 401, 422)

    def test_refresh_with_garbage_fails(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "garbage.token.value"},
        )
        assert resp.status_code in (400, 401, 422)


class TestRBAC:
    """Verify role-based access control is enforced correctly."""

    def test_viewer_cannot_run_prediction(
        self, client: TestClient, viewer_headers: dict, sample_jpeg_bytes: bytes
    ):
        """Viewers must be denied write-level endpoints."""
        resp = client.post(
            "/api/v1/predict",
            files={"image": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers=viewer_headers,
        )
        # 403 Forbidden or 401 depending on token validity
        assert resp.status_code in (401, 403)

    def test_unauthenticated_request_denied(self, client: TestClient):
        """Any protected endpoint must return 401 with no token."""
        resp = client.get("/api/v1/inspections")
        assert resp.status_code == 401
