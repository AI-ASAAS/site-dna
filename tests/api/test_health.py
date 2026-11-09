"""API endpoint integration tests for health and readiness probes."""

import pytest
from fastapi.testclient import TestClient

from site_dna.api.main import create_app
from site_dna.core.config import Settings, get_settings


def test_health_endpoint_returns_200():
    """Verify GET /api/v1/health returns HTTP 200 and expected metadata."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "site-dna"
    assert data["version"] == "0.1.0"
    assert data["phase"] == "01"


def test_readiness_returns_200_when_key_configured(monkeypatch: pytest.MonkeyPatch):
    """Verify GET /api/v1/ready returns HTTP 200 when credentials are present."""
    test_settings = Settings(
        gemini_api_key="valid_dummy_key_12345",
        gemini_model="gemini-3.6-flash",
        app_env="test",
    )
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings
    client = TestClient(app)

    response = client.get("/api/v1/ready")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["ready"] is True
    assert data["details"]["backend_running"] is True
    assert data["details"]["api_key_configured"] is True
    assert data["details"]["model_configured"] == "gemini-3.6-flash"
    assert data["details"]["live_connectivity_verified"] is False
    # Ensure no secrets leak
    assert "valid_dummy_key" not in response.text


def test_readiness_returns_503_when_key_missing(monkeypatch: pytest.MonkeyPatch):
    """Verify GET /api/v1/ready returns HTTP 503 when credentials are absent."""
    test_settings = Settings(
        gemini_api_key=None,
        gemini_model="gemini-3.6-flash",
        app_env="test",
    )
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings
    client = TestClient(app)

    response = client.get("/api/v1/ready")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unready"
    assert data["ready"] is False
    assert data["details"]["api_key_configured"] is False
    assert "not configured" in data["message"].lower()


def test_openapi_and_docs_available():
    """Verify that OpenAPI JSON schema and Swagger UI /docs are accessible."""
    app = create_app()
    client = TestClient(app)

    docs_resp = client.get("/docs")
    assert docs_resp.status_code == 200
    assert "swagger" in docs_resp.text.lower() or "html" in docs_resp.headers.get("content-type", "")

    schema_resp = client.get("/openapi.json")
    assert schema_resp.status_code == 200
    schema = schema_resp.json()
    assert "openapi" in schema
    assert "/api/v1/health" in schema["paths"]
    assert "/api/v1/ready" in schema["paths"]
