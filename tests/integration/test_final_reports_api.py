"""Integration tests for Phase 12 Final Reports API endpoints."""

import pytest
from fastapi.testclient import TestClient
from site_dna.api.main import create_app


def test_final_reports_api_lifecycle():
    """Verify end-to-end report API: list, retrieve metadata, download PDF, and HTML preview."""
    app = create_app()
    client = TestClient(app)

    # 1. List existing reports for crawl-a
    list_resp = client.get("/api/v1/reports/final/crawl-a")
    assert list_resp.status_code == 200
    reports = list_resp.json()
    assert isinstance(reports, list)

    # If reports already generated (from CLI run), test retrieval
    if len(reports) > 0:
        rep = reports[0]
        rep_id = rep["report_id"]

        # 2. Get Report Metadata
        meta_resp = client.get(f"/api/v1/reports/final/crawl-a/{rep_id}")
        assert meta_resp.status_code == 200
        meta = meta_resp.json()
        assert meta["report_id"] == rep_id
        assert meta["crawl_run_id"] == "crawl-a"
        assert meta["page_count"] >= 1

        # 3. Preview HTML
        preview_resp = client.get(f"/api/v1/reports/final/crawl-a/{rep_id}/preview")
        assert preview_resp.status_code == 200
        assert "text/html" in preview_resp.headers["content-type"]
        assert "Site DNA" in preview_resp.text or "أساس" in preview_resp.text

        # 4. Download PDF
        dl_resp = client.get(f"/api/v1/reports/final/crawl-a/{rep_id}/download?format=pdf")
        assert dl_resp.status_code == 200
        assert "application/pdf" in dl_resp.headers["content-type"]
        assert len(dl_resp.content) > 1000

        # 5. List Artifacts
        art_resp = client.get(f"/api/v1/reports/final/crawl-a/{rep_id}/artifacts")
        assert art_resp.status_code == 200
        artifacts = art_resp.json()
        assert "artifacts" in artifacts
        assert artifacts["artifacts"]["pdf"]["exists"] is True


def test_final_reports_api_input_validation():
    """Verify input validation rejecting invalid run IDs or non-existent reports."""
    app = create_app()
    client = TestClient(app)

    # Path traversal / invalid ID check
    resp = client.get("/api/v1/reports/final/../../../etc/passwd")
    assert resp.status_code in (400, 404)

    # Non-existent run
    resp2 = client.get("/api/v1/reports/final/nonexistent-run-12345/nonexistent-rep")
    assert resp2.status_code == 404
