"""API tests for Site DNA Phase 07.5 Runs, Orchestration and Dashboard endpoints."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from site_dna.api.main import create_app
from site_dna.api.routes.runs import get_coordinator
from site_dna.core.config import Settings, get_settings
from site_dna.orchestration.coordinator import AnalysisCoordinator


@pytest.fixture
def test_env(tmp_path: Path):
    """Set up an isolated test coordinator and client."""
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    settings = Settings(
        gemini_api_key="dummy_test_key_for_api_suite_12345",
        gemini_model="gemini-3.6-flash",
        app_env="test",
    )

    coordinator = AnalysisCoordinator(base_dir=runs_dir, settings=settings)

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_coordinator] = lambda: coordinator

    client = TestClient(app)
    return {
        "client": client,
        "coordinator": coordinator,
        "runs_dir": runs_dir,
    }


def test_list_agents_endpoint(test_env):
    """Verify GET /api/v1/agents returns all 12 agents with complete readiness."""
    client = test_env["client"]
    response = client.get("/api/v1/agents")

    assert response.status_code == 200
    agents = response.json()
    assert len(agents) == 12

    # In Phase 12 Final Release Candidate, all 12 agents are fully implemented
    for a in agents:
        assert a["implementation_status"] == "implemented"
        if a["phase"] > 1:
            assert a["can_execute"] is True
            assert a["runtime_availability"] == "ready"


def test_get_agent_by_id(test_env):
    """Verify GET /api/v1/agents/{agent_id} returns single agent or 404."""
    client = test_env["client"]

    # Known agent
    response = client.get("/api/v1/agents/visual_identity")
    assert response.status_code == 200
    agent = response.json()
    assert agent["id"] == "visual_identity"
    assert agent["phase"] == 4
    assert agent["can_execute"] is True

    # Unknown agent
    response_404 = client.get("/api/v1/agents/non_existent_agent_xyz")
    assert response_404.status_code == 404


def test_get_dashboard_summary(test_env):
    """Verify GET /api/v1/dashboard/summary returns aggregations."""
    client = test_env["client"]
    response = client.get("/api/v1/dashboard/summary")

    assert response.status_code == 200
    summary = response.json()
    assert "total_runs" in summary
    assert "running_runs" in summary
    assert "completed_runs" in summary
    assert "failed_runs" in summary
    assert "agent_readiness" in summary
    assert "recent_runs" in summary


def test_list_runs_empty(test_env):
    """Verify GET /api/v1/runs returns paginated structure."""
    client = test_env["client"]
    response = client.get("/api/v1/runs")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert data["total"] == 0
    assert len(data["items"]) == 0


def test_reject_unknown_agents_on_run_submission(test_env):
    """Verify POST /api/v1/runs rejects unknown stage with HTTP 400."""
    client = test_env["client"]

    payload = {
        "url": "https://example.com",
        "stages": ["discovery", "unknown_unregistered_stage_xyz"],
    }
    response = client.post("/api/v1/runs", json=payload)
    assert response.status_code == 400


def test_reject_invalid_url_on_run_submission(test_env):
    """Verify POST /api/v1/runs rejects non-http URLs with HTTP 400 or 422."""
    client = test_env["client"]

    payload = {
        "url": "javascript:alert(1)",
        "stages": ["discovery"],
    }
    response = client.post("/api/v1/runs", json=payload)
    assert response.status_code in (400, 422)


def test_submit_valid_run_selective_stages(test_env):
    """Verify POST /api/v1/runs successfully initializes a run with selective stages."""
    client = test_env["client"]
    coordinator = test_env["coordinator"]

    # Prevent background async task from executing actual pipelines during test
    with patch.object(coordinator, "_execute_pipeline"):
        payload = {
            "url": "https://example.com",
            "stages": ["visual_capture", "technical_seo"],
        }
        response = client.post("/api/v1/runs", json=payload)

        assert response.status_code == 201
        run_record = response.json()
        assert run_record["url"] == "https://example.com"
        assert run_record["status"] in ("queued", "running")
        # Ensure discovery is automatically resolved as dependency
        stages = run_record["stages"]
        assert "discovery" in stages
        assert "visual_capture" in stages
        assert "technical_seo" in stages

        # Verify get run by id
        run_id = run_record["run_id"]
        get_res = client.get(f"/api/v1/runs/{run_id}")
        assert get_res.status_code == 200
        assert get_res.json()["run_id"] == run_id


def test_get_nonexistent_run_returns_404(test_env):
    """Verify GET /api/v1/runs/{run_id} returns 404 for missing runs."""
    client = test_env["client"]
    response = client.get("/api/v1/runs/non-existent-run-id-999")
    assert response.status_code == 404


def test_screenshot_path_traversal_protection(test_env):
    """Verify GET /api/v1/runs/{run_id}/artifacts/screenshot prevents path traversal."""
    client = test_env["client"]
    response = client.get(
        "/api/v1/runs/test-run/artifacts/screenshot",
        params={"file": "../../../etc/passwd"},
    )
    assert response.status_code in (400, 403, 404)
