"""API endpoint integration tests for POST /api/v1/analysis/visual-identity."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from site_dna.api.main import app
from site_dna.core.config import Settings, get_settings
from site_dna.schemas.visual_identity import VisualIdentityReport


@pytest.fixture(autouse=True)
def enable_visual_analysis_api():
    """Ensure visual analysis API is enabled during API tests."""
    custom_settings = Settings(visual_analysis_api_enabled=True, app_env="test")
    app.dependency_overrides[get_settings] = lambda: custom_settings
    yield
    app.dependency_overrides.pop(get_settings, None)


def test_api_visual_identity_not_found():
    """Verify that a non-existent visual run returns 404 Not Found."""
    client = TestClient(app)
    response = client.post(
        "/api/v1/analysis/visual-identity",
        json={"visual_run_id": "vis-non-existent-9999"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_api_visual_identity_success():
    """Verify successful execution returning VisualIdentityReport structure."""
    client = TestClient(app)

    mock_report = VisualIdentityReport(
        analysis_run_id="vi-test123456",
        crawl_run_id="crawl-mock",
        visual_run_id="vis-mock",
        site_url="https://example.com",
        analysis_status="completed",
        summary_arabic="ملخص تحليلي تجريبي للهوية البصرية.",
        summary_english="Experimental visual identity summary.",
        overall_score=88.5,
    )

    with patch(
        "site_dna.api.routes.visual_identity.VisualIdentityAnalysisService.analyze_visual_identity",
        return_value=mock_report,
    ):
        response = client.post(
            "/api/v1/analysis/visual-identity",
            json={"visual_run_id": "vis-mock", "save_results": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_run_id"] == "vi-test123456"
        assert data["overall_score"] == 88.5
        assert data["analysis_status"] == "completed"
