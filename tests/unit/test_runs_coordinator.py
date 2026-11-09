"""Unit tests for Site DNA AnalysisCoordinator and Agent Registry."""

import pytest
from fastapi import HTTPException

from site_dna.orchestration.coordinator import AnalysisCoordinator
from site_dna.schemas.runs import RunSubmissionRequest


def test_agent_registry_coverage():
    """Verify that all 12 phases (Phases 01-12) are properly registered with exact capabilities."""
    coordinator = AnalysisCoordinator()
    agents = coordinator.list_agents()

    assert len(agents) == 12
    phases = [a.phase for a in agents]
    assert phases == list(range(1, 13))

    # Phase 01: Infrastructure (implemented, not independently executable)
    phase_01 = next(a for a in agents if a.phase == 1)
    assert phase_01.implementation_status == "implemented"
    assert phase_01.can_execute is False

    # Phases 02-12: All implemented and executable in Phase 12 release candidate
    for p in range(2, 13):
        agent = next(a for a in agents if a.phase == p)
        assert agent.implementation_status == "implemented"
        assert agent.can_execute is True
        assert agent.runtime_availability == "ready"


def test_unknown_agents_execution_rejection():
    """Verify that attempting to execute an unknown agent is rejected with HTTP 400."""
    coordinator = AnalysisCoordinator()

    # Attempt to execute unregistered agent
    req = RunSubmissionRequest(
        url="https://example.com",
        stages=["discovery", "unknown_future_agent_xyz"],
    )
    with pytest.raises(HTTPException) as exc_info:
        coordinator.create_and_start_run(req)

    assert exc_info.value.status_code == 400


def test_invalid_url_rejection():
    """Verify URL format validation rejecting invalid or non-http protocols."""
    coordinator = AnalysisCoordinator()

    req = RunSubmissionRequest(url="ftp://invalid.com", stages=["discovery"])
    with pytest.raises(HTTPException) as exc_info:
        coordinator.create_and_start_run(req)

    assert exc_info.value.status_code == 400
    assert "Invalid URL" in exc_info.value.detail


def test_screenshot_path_traversal_rejection():
    """Verify path traversal protection on screenshot file resolution."""
    coordinator = AnalysisCoordinator()

    with pytest.raises(HTTPException) as exc_info:
        coordinator.resolve_screenshot_path("run-test", "../../etc/passwd")

    assert exc_info.value.status_code in (400, 403, 404)
