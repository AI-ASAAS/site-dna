"""Integration tests for Phase 11 Strategic Intelligence API endpoints."""

from fastapi.testclient import TestClient
from site_dna.api.main import create_app


def test_strategic_api_full_workflow():
    """Verify end-to-end API lifecycle: trigger, retrieve, inspect actions, and patch status."""
    app = create_app()
    client = TestClient(app)

    # 1. Trigger Strategic Analysis on crawl-a
    resp = client.post(
        "/api/v1/analysis/strategy",
        json={
            "crawl_run_id": "crawl-a",
            "language": "ar",
            "deterministic_only": True,
            "save_results": True,
        },
    )
    assert resp.status_code in (200, 201), f"Trigger failed: {resp.text}"
    report_data = resp.json()
    assert report_data["crawl_run_id"] == "crawl-a"
    assert "strategic_run_id" in report_data
    assert len(report_data["actions"]) > 0
    first_action_id = report_data["actions"][0]["action_id"]

    # 2. GET /api/v1/analysis/strategy/{crawl_run_id}
    resp_get = client.get("/api/v1/analysis/strategy/crawl-a")
    assert resp_get.status_code == 200
    assert resp_get.json()["strategic_run_id"] == report_data["strategic_run_id"]

    # 3. GET /api/v1/analysis/strategy/{crawl_run_id}/actions
    resp_actions = client.get("/api/v1/analysis/strategy/crawl-a/actions")
    assert resp_actions.status_code == 200
    actions_list = resp_actions.json()
    assert isinstance(actions_list, list)
    assert len(actions_list) > 0

    # 4. GET /api/v1/analysis/strategy/{crawl_run_id}/conflicts
    resp_conflicts = client.get("/api/v1/analysis/strategy/crawl-a/conflicts")
    assert resp_conflicts.status_code == 200
    assert isinstance(resp_conflicts.json(), list)

    # 5. GET /api/v1/analysis/strategy/{crawl_run_id}/roadmap
    resp_roadmap = client.get("/api/v1/analysis/strategy/crawl-a/roadmap")
    assert resp_roadmap.status_code == 200
    roadmap_data = resp_roadmap.json()
    assert isinstance(roadmap_data, list)
    assert len(roadmap_data) == 4
    assert roadmap_data[0]["wave_number"] == 1

    # 6. PATCH /api/v1/analysis/strategy/{crawl_run_id}/actions/{action_id}
    resp_patch = client.patch(
        f"/api/v1/analysis/strategy/crawl-a/actions/{first_action_id}",
        json={
            "status": "in_progress",
            "notes": "Assigned to Sprint 12 Frontend squad.",
        },
    )
    assert resp_patch.status_code == 200
    patched_action = resp_patch.json()
    assert patched_action["action_id"] == first_action_id
    assert patched_action["status"] == "success"
    assert patched_action["new_status"] == "in_progress"
    assert patched_action["notes"] == "Assigned to Sprint 12 Frontend squad."

    # 7. GET Coordinator Report for Strategic Intelligence
    resp_report = client.get("/api/v1/runs/crawl-a/reports/strategic_intelligence")
    assert resp_report.status_code == 200
    assert "content" in resp_report.json()
    assert "# تقرير الذكاء الاستراتيجي" in resp_report.json()["content"]
