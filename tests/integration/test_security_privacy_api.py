"""Integration tests for Site DNA Phase 09 Security & Privacy FastAPI endpoints."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from site_dna.api.main import app


@pytest.fixture
def client():
    """Create a FastAPI TestClient instance."""
    return TestClient(app)


def test_security_privacy_api_flow(tmp_path: Path, monkeypatch, client: TestClient):
    """Verify POST and GET endpoints for security & privacy intelligence."""
    runs_dir = tmp_path / "runs"
    crawl_dir = runs_dir / "crawl-api-test-01"
    crawl_dir.mkdir(parents=True)

    crawl_payload = {
        "target_url": "https://api-sec.example.com/",
        "website_info": {"canonical_origin": "https://api-sec.example.com"},
        "pages": [
            {
                "url": "https://api-sec.example.com/",
                "status_code": 200,
                "headers": {
                    "strict-transport-security": "max-age=31536000",
                    "content-security-policy": "default-src 'self'",
                    "x-frame-options": "DENY",
                    "x-content-type-options": "nosniff",
                },
                "cookies": [],
                "raw_html": "<html><body><a href='/privacy'>Privacy Policy</a></body></html>",
            }
        ],
    }
    (crawl_dir / "crawl.json").write_text(json.dumps(crawl_payload), encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    # 1. Trigger security analysis via POST
    trigger_resp = client.post(
        "/api/v1/analysis/security-privacy",
        json={
            "crawl_run_id": "crawl-api-test-01",
            "deterministic_only": True,
            "max_pages": 4,
        },
    )
    assert trigger_resp.status_code == 201
    report = trigger_resp.json()
    assert report["crawl_run_id"] == "crawl-api-test-01"
    assert report["scores"]["overall_score"] > 0
    assert "https_assessment" in report

    # 2. Retrieve analysis via GET
    get_resp = client.get("/api/v1/analysis/security-privacy/crawl-api-test-01")
    assert get_resp.status_code == 200
    retrieved = get_resp.json()
    assert retrieved["crawl_run_id"] == "crawl-api-test-01"

    # 3. Retrieve security headers breakdown
    hdr_resp = client.get("/api/v1/analysis/security-privacy/crawl-api-test-01/headers")
    assert hdr_resp.status_code == 200
    hdrs = hdr_resp.json()
    assert "present_headers_count" in hdrs

    # 4. 404 for nonexistent run
    bad_resp = client.get("/api/v1/analysis/security-privacy/nonexistent-run")
    assert bad_resp.status_code == 404
