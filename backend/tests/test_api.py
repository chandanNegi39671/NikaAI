from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "degraded"]


def test_login_missing_credentials():
    response = client.post("/api/v1/auth/login", data={})
    # OAuth2PasswordBearer expects form data with username and password
    assert response.status_code == 422
