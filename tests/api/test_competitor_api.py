"""API route tests for Phase 08 Competitor Intelligence endpoints."""

from fastapi.testclient import TestClient

from site_dna.api.main import create_app


def test_competitor_api_endpoints():
    app = create_app()
    client = TestClient(app)

    # 1. Non-existent competitor run
    resp = client.get("/api/v1/analysis/competitors/non-existent-comp-id")
    assert resp.status_code == 404

    # 2. Non-existent matrix
    resp_matrix = client.get("/api/v1/analysis/competitors/non-existent-comp-id/matrix")
    assert resp_matrix.status_code == 404


def test_runs_submission_with_competitor_urls():
    app = create_app()
    client = TestClient(app)

    payload = {
        "url": "https://test-primary.example.com",
        "stages": ["discovery", "competitor_intelligence"],
        "competitor_urls": ["https://test-competitor.example.com"],
        "offline_mode": True,
        "max_pages": 1,
    }

    resp = client.post("/api/v1/runs", json=payload)
    assert resp.status_code in (200, 201)
    data = resp.json()
    assert "run_id" in data
    assert "competitor_intelligence" in data["stages"]
