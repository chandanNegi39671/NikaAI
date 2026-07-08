"""
backend/tests/conftest.py
──────────────────────────
Pytest fixtures shared across the entire test suite.

Architecture:
  - An in-memory SQLite database is created for every test session.
  - Tables are created from the real SQLAlchemy models (not mocked).
  - FastAPI dependency overrides replace get_db() with the test session.
  - A TestClient wraps the real FastAPI app so all middleware/routes run.
  - Auth helpers create real JWT tokens without touching the DB.
"""

from __future__ import annotations

import io
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.database import Base, get_db
from app.core.auth import create_access_token, get_password_hash
from app.main import app
from app.models.db_models import User, Machine, Worker, Shift


# ── Test database ─────────────────────────────────────────────────────────────

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    """Create all database tables once for the entire test session."""
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Provide an isolated DB session per test, rolled back after each test."""
    connection = engine_test.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    """FastAPI TestClient with the real app and DB dependency overridden."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


# ── User fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture()
def admin_user(db_session: Session) -> User:
    """Create and persist a test admin user."""
    user = User(
        username="test_admin",
        email="admin@test.nika.ai",
        password_hash=get_password_hash("admin_password"),
        role="admin",
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture()
def operator_user(db_session: Session) -> User:
    """Create and persist a test operator user."""
    user = User(
        username="test_operator",
        email="operator@test.nika.ai",
        password_hash=get_password_hash("operator_password"),
        role="operator",
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture()
def viewer_user(db_session: Session) -> User:
    """Create and persist a test viewer user."""
    user = User(
        username="test_viewer",
        email="viewer@test.nika.ai",
        password_hash=get_password_hash("viewer_password"),
        role="viewer",
    )
    db_session.add(user)
    db_session.flush()
    return user


# ── Token fixtures ────────────────────────────────────────────────────────────

@pytest.fixture()
def admin_token(admin_user: User) -> str:
    """Return a valid JWT access token for the admin user."""
    return create_access_token(subject=admin_user.username, role=admin_user.role)


@pytest.fixture()
def operator_token(operator_user: User) -> str:
    """Return a valid JWT access token for the operator user."""
    return create_access_token(subject=operator_user.username, role=operator_user.role)


@pytest.fixture()
def viewer_token(viewer_user: User) -> str:
    """Return a valid JWT access token for the viewer user."""
    return create_access_token(subject=viewer_user.username, role=viewer_user.role)


# ── Helper functions ──────────────────────────────────────────────────────────

def auth_headers(token: str) -> dict:
    """Build Authorization header dict from a JWT token string."""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_headers(admin_token: str) -> dict:
    return auth_headers(admin_token)


@pytest.fixture()
def operator_headers(operator_token: str) -> dict:
    return auth_headers(operator_token)


@pytest.fixture()
def viewer_headers(viewer_token: str) -> dict:
    return auth_headers(viewer_token)


# ── Image fixtures ────────────────────────────────────────────────────────────

@pytest.fixture()
def sample_jpeg_bytes() -> bytes:
    """Return bytes of a minimal valid JPEG image (100×100 px red square)."""
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture()
def sample_png_bytes() -> bytes:
    """Return bytes of a minimal valid PNG image (100×100 px blue square)."""
    img = Image.new("RGB", (100, 100), color=(0, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture()
def too_small_image_bytes() -> bytes:
    """Return bytes of a JPEG image that is too small (10×10 px) to pass validation."""
    img = Image.new("RGB", (10, 10), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ── Machine fixtures ──────────────────────────────────────────────────────────

@pytest.fixture()
def sample_machine(db_session: Session) -> Machine:
    """Create and persist a test machine."""
    machine = Machine(
        name="Test CNC Press",
        model_number="CNC-TEST-01",
        status="operational",
        location="Test Zone A",
    )
    db_session.add(machine)
    db_session.flush()
    return machine


@pytest.fixture(autouse=True)
def mock_celery_task(monkeypatch):
    """Globally mock Celery delay connections to avoid tests hanging on Redis."""
    from unittest.mock import MagicMock
    from app.services.tasks import run_yolo_inference

    mock_delay = MagicMock()
    mock_result = MagicMock()
    mock_result.get.return_value = {
        "success": True,
        "detections": [
            {
                "defect": "surface_crack",
                "confidence": 0.92,
                "bounding_box": {"x1": 10.0, "y1": 20.0, "x2": 200.0, "y2": 300.0}
            }
        ],
        "inference_time_ms": 43.2,
        "image_width": 100,
        "image_height": 100
    }
    mock_delay.return_value = mock_result
    monkeypatch.setattr(run_yolo_inference, "delay", mock_delay)
