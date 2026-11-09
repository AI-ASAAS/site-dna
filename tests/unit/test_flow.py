"""Unit tests for Foundation Flow execution and state management."""

from unittest.mock import MagicMock, patch

import pytest

from site_dna.core.config import Settings
from site_dna.flows.foundation_flow import FoundationFlow
from site_dna.schemas.health import SmokeAgentOutput


def test_flow_state_initializes():
    """Verify that flow initializes state attributes correctly on startup."""
    settings = Settings(
        app_name="Site DNA",
        gemini_model="gemini-3.6-flash",
        gemini_api_key="test_key",
    )
    flow = FoundationFlow(settings=settings)

    run_id = flow.initialize_workflow()

    assert run_id.startswith("flow-")
    assert flow.state.run_id == run_id
    assert flow.state.model_name == "gemini-3.6-flash"
    assert flow.state.execution_status == "initialized"
    assert flow.state.started_at is not None


@patch("site_dna.flows.foundation_flow.run_smoke_crew")
def test_flow_successful_execution(mock_run_crew: MagicMock):
    """Verify end-to-end Flow execution with mocked CrewAI output."""
    mock_run_crew.return_value = SmokeAgentOutput(
        project="Site DNA",
        status="operational",
        message="CrewAI Gemini integration successful",
    )

    settings = Settings(
        app_name="Site DNA",
        gemini_model="gemini-3.6-flash",
        gemini_api_key="test_key",
    )
    flow = FoundationFlow(settings=settings)

    flow.kickoff()

    assert flow.state.execution_status == "completed"
    assert flow.state.run_id.startswith("flow-")
    assert flow.state.completed_at is not None
    assert flow.state.agent_output is not None
    assert flow.state.agent_output.project == "Site DNA"
    assert flow.state.agent_output.status == "operational"
    assert flow.state.agent_output.message == "CrewAI Gemini integration successful"
    assert flow.state.error_message is None
    mock_run_crew.assert_called_once()


@patch("site_dna.flows.foundation_flow.run_smoke_crew")
def test_flow_failure_recording(mock_run_crew: MagicMock):
    """Verify that flow transitions to 'failed' state when agent execution fails."""
    mock_run_crew.side_effect = RuntimeError("Simulated agent connection failure")

    settings = Settings(
        app_name="Site DNA",
        gemini_model="gemini-3.6-flash",
        gemini_api_key="test_key",
    )
    flow = FoundationFlow(settings=settings)

    with pytest.raises(RuntimeError):
        flow.kickoff()

    assert flow.state.execution_status == "failed"
    assert flow.state.completed_at is not None
    assert "Simulated agent connection failure" in (flow.state.error_message or "")
    assert flow.state.agent_output is None
