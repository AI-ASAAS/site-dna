"""Security and boundary tests for Phase 11 Strategic Intelligence."""

import pytest
from fastapi.testclient import TestClient

from site_dna.analysis.strategic_intelligence.context_builder import StrategicContextBuilder
from site_dna.api.main import create_app


def test_path_traversal_rejection_in_api():
    """Verify API strictly rejects path traversal in crawl_run_id."""
    app = create_app()
    client = TestClient(app)

    malicious_ids = [
        "../../etc/passwd",
        "..\\..\\windows\\system32",
        "crawl-a/../../../secret",
    ]

    for m_id in malicious_ids:
        resp = client.get(f"/api/v1/analysis/strategy/{m_id}")
        assert resp.status_code in (400, 404, 422)


def test_action_status_patch_rejects_invalid_states():
    """Verify PATCH /actions/{action_id} rejects unauthorized status transitions."""
    app = create_app()
    client = TestClient(app)

    resp = client.patch(
        "/api/v1/analysis/strategy/crawl-a/actions/act-dummy",
        json={"status": "DROP_TABLE_USERS"},
    )
    assert resp.status_code == 422


def test_builder_path_traversal_patterns():
    """Direct verification of context builder regex input sanitization."""
    from site_dna.schemas.strategic_intelligence import StrategicAnalysisRequest

    builder = StrategicContextBuilder()
    with pytest.raises(ValueError):
        req = StrategicAnalysisRequest(crawl_run_id="run-123/../../hack")
        builder.build_context(req)
