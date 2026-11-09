"""API tests for POST /api/v1/discovery endpoint access control and schema."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from site_dna.api.main import create_app
from site_dna.core.config import Settings, get_settings
from site_dna.schemas.discovery import CrawlResult, CrawlStatistics, WebsiteInfo


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_discovery_api_disabled_by_default_returns_403():
    custom_settings = Settings(
        discovery_api_enabled=False,
        app_env="test",
    )
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: custom_settings
    client = TestClient(app)

    response = client.post(
        "/api/v1/discovery",
        json={"url": "https://example.com"},
    )
    assert response.status_code == 403
    assert "disabled" in response.json()["detail"].lower()


def test_discovery_api_requires_bearer_token_when_configured():
    custom_settings = Settings(
        discovery_api_enabled=True,
        discovery_api_token="secret-token-123",
        app_env="test",
    )

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: custom_settings
    client = TestClient(app)

    # Missing header
    resp = client.post("/api/v1/discovery", json={"url": "https://example.com"})
    assert resp.status_code == 401

    # Incorrect token
    resp = client.post(
        "/api/v1/discovery",
        json={"url": "https://example.com"},
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert resp.status_code == 401


def test_discovery_api_success_mocked():
    custom_settings = Settings(
        discovery_api_enabled=True,
        discovery_api_token="test-token",
        app_env="test",
    )

    mock_result = CrawlResult(
        run_id="test-run-123",
        website_info=WebsiteInfo(
            initial_url="https://example.com",
            canonical_origin="https://example.com",
        ),
        pages=[],
        discovered_internal_links=["https://example.com/about"],
        evidence=[],
        errors=[],
        statistics=CrawlStatistics(total_pages_crawled=1),
    )

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: custom_settings

    with patch("site_dna.discovery.service.WebsiteDiscoveryService.discover", new_callable=AsyncMock) as mock_disc:
        mock_disc.return_value = mock_result

        client = TestClient(app)
        resp = client.post(
            "/api/v1/discovery",
            json={"url": "https://example.com", "max_pages": 3},
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["run_id"] == "test-run-123"
        assert data["website_info"]["canonical_origin"] == "https://example.com"
        assert data["statistics"]["total_pages_crawled"] == 1
