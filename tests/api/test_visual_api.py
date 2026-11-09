"""Tests for the visual capture FastAPI endpoint."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from site_dna.api.main import app
from site_dna.core.config import Settings, get_settings
from site_dna.schemas.discovery import CrawlResult, WebsiteInfo
from site_dna.schemas.visual import VisualCaptureResult, VisualCaptureStatistics


@pytest.fixture
def client():
    return TestClient(app)


def test_visual_api_disabled_by_default_returns_403(client: TestClient):
    # Override settings so visual_api_enabled is False
    custom_settings = Settings(visual_api_enabled=False, app_env="test")
    app.dependency_overrides[get_settings] = lambda: custom_settings
    try:
        response = client.post(
            "/api/v1/visual/capture",
            json={"crawl_run_id": "test-123"},
        )
        assert response.status_code == 403
        assert "disabled" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_settings, None)


def test_visual_api_token_auth_required_when_configured(client: TestClient):
    custom_settings = Settings(
        visual_api_enabled=True,
        visual_api_token=SecretStr("supersecrettoken"),
        app_env="test",
    )
    app.dependency_overrides[get_settings] = lambda: custom_settings
    try:
        # Missing auth
        res_missing = client.post(
            "/api/v1/visual/capture",
            json={"crawl_run_id": "test-123"},
        )
        assert res_missing.status_code == 401

        # Wrong token
        res_wrong = client.post(
            "/api/v1/visual/capture",
            json={"crawl_run_id": "test-123"},
            headers={"Authorization": "Bearer wrongtoken"},
        )
        assert res_wrong.status_code == 401
    finally:
        app.dependency_overrides.pop(get_settings, None)


def test_visual_api_path_traversal_rejected(client: TestClient):
    custom_settings = Settings(visual_api_enabled=True, app_env="test")
    app.dependency_overrides[get_settings] = lambda: custom_settings
    try:
        response = client.post(
            "/api/v1/visual/capture",
            json={"crawl_file": "../../etc/passwd"},
        )
        assert response.status_code == 400
        assert "Path traversal" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_settings, None)


def test_visual_api_crawl_file_not_found(client: TestClient):
    custom_settings = Settings(visual_api_enabled=True, app_env="test")
    app.dependency_overrides[get_settings] = lambda: custom_settings
    try:
        response = client.post(
            "/api/v1/visual/capture",
            json={"crawl_run_id": "nonexistent-run-9999"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_settings, None)


def test_visual_api_successful_capture_mocked(client: TestClient, tmp_path: Path):
    custom_settings = Settings(
        visual_api_enabled=True,
        visual_capture_enabled=True,
        app_env="test",
    )
    app.dependency_overrides[get_settings] = lambda: custom_settings

    # Create dummy crawl.json
    crawl_result = CrawlResult(
        run_id="run-api-test-1",
        status="completed",
        website_info=WebsiteInfo(
            initial_url="https://example.com/",
            canonical_origin="https://example.com",
        ),
        pages=[],
    )
    crawl_file = tmp_path / "crawl.json"
    crawl_file.write_text(crawl_result.model_dump_json(), encoding="utf-8")

    mock_capture_result = VisualCaptureResult(
        crawl_run_id="run-api-test-1",
        visual_run_id="vis-api-1",
        status="completed",
        target_origin="https://example.com",
        pages=[],
        statistics=VisualCaptureStatistics(),
    )

    with patch(
        "site_dna.visual.service.VisualCollectionService.collect_visual_evidence",
        new=AsyncMock(return_value=mock_capture_result),
    ):
        try:
            response = client.post(
                "/api/v1/visual/capture",
                json={"crawl_file": str(crawl_file)},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["crawl_run_id"] == "run-api-test-1"
            assert data["visual_run_id"] == "vis-api-1"
            assert data["status"] == "completed"
        finally:
            app.dependency_overrides.pop(get_settings, None)
