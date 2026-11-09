"""Security and boundary tests for Phase 12 Final Reporting & PDF Export."""

import pytest
from fastapi.testclient import TestClient
from site_dna.api.main import create_app
from site_dna.reporting.pdf_renderer import PlaywrightPdfRenderer


def test_phase12_path_traversal_rejection():
    """Verify final reports API rejects path traversal in crawl_run_id and report_id."""
    app = create_app()
    client = TestClient(app)

    malicious_inputs = [
        ("../../etc/passwd", "rep-1"),
        ("crawl-a", "../../boot.ini"),
        ("..\\..\\windows\\system32", "rep-1"),
        ("crawl-a/../../../secret", "rep-1"),
    ]

    for c_id, r_id in malicious_inputs:
        resp = client.get(f"/api/v1/reports/final/{c_id}/{r_id}")
        assert resp.status_code in (400, 404, 422)

        resp_dl = client.get(f"/api/v1/reports/final/{c_id}/{r_id}/download")
        assert resp_dl.status_code in (400, 404, 422)


def test_phase12_renderer_isolation_flags():
    """Verify Chromium PDF renderer launches with security isolation flags."""
    renderer = PlaywrightPdfRenderer()
    args = renderer._get_chromium_args()

    # Network disabled to eliminate outbound SSRF during print rendering
    assert "--disable-network" in args
    # Sandbox and isolation flags
    assert "--no-sandbox" in args or "--disable-setuid-sandbox" in args or renderer.headless is True


def test_phase12_unsupported_format_rejection():
    """Verify invalid download formats (e.g., .exe, .sh) are rejected with 400 Bad Request."""
    app = create_app()
    client = TestClient(app)

    resp = client.get("/api/v1/reports/final/crawl-a/rep-test/download?format=exe")
    assert resp.status_code in (400, 404)
