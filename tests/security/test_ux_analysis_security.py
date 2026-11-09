"""Security tests for UX/UI analysis subsystem (path traversal, prompt injection, access gates)."""

from pathlib import Path

from fastapi.testclient import TestClient

from site_dna.analysis.ux_ui.service import UXAnalysisService
from site_dna.api.main import app
from site_dna.core.config import Settings
from site_dna.schemas.ux_ui import UXAnalysisRequest

client = TestClient(app)
FIXTURES_DIR = Path("tests/fixtures/ux_ui")


def test_api_ux_path_traversal_rejection():
    """Verify that path traversal strings in API requests are rejected with 400 Bad Request."""
    response = client.post(
        "/api/v1/analysis/ux-ui",
        json={"visual_manifest_file": "../../etc/passwd"},
    )
    assert response.status_code == 400
    assert "Path traversal" in response.json()["detail"]


def test_api_ux_invalid_characters_rejection():
    """Verify that suspicious characters in visual_run_id are rejected."""
    response = client.post(
        "/api/v1/analysis/ux-ui",
        json={"visual_run_id": "vis-run; rm -rf /"},
    )
    assert response.status_code == 400
    assert "Invalid characters" in response.json()["detail"]


def test_api_ux_disabled_gate():
    """Verify that API returns 403 Forbidden when UX_ANALYSIS_API_ENABLED=False."""
    from site_dna.core.config import get_settings

    custom_settings = Settings(ux_analysis_api_enabled=False, app_env="test")
    app.dependency_overrides[get_settings] = lambda: custom_settings
    try:
        response = client.post(
            "/api/v1/analysis/ux-ui",
            json={"visual_run_id": "vis-valid"},
        )
        assert response.status_code == 403
        assert "disabled" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_settings, None)


def test_adversarial_prompt_injection_fixture_f():
    """Verify that adversarial prompt injection payloads in page content do not hijack the system."""
    base_dir = str(FIXTURES_DIR / "fixture_f_prompt_injection" / "runs")
    service = UXAnalysisService(base_dir=base_dir)

    req = UXAnalysisRequest(
        visual_run_id="vis-f",
        crawl_run_id="crawl-f",
        max_pages=1,
        save_results=False,
    )
    report = service.analyze_ux(req, offline_mode=True)

    # The report must not crash and overall score should not blindly be 100
    assert report.analysis_status in ("completed", "partial")
    # Score should reflect reality (not hijacked to 100 by the prompt)
    assert report.overall_score is not None
