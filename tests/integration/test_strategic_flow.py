"""Integration tests for Phase 11 CrewAI Strategic Flow."""

from site_dna.flows.strategic_intelligence_flow import StrategicFlowState, StrategicIntelligenceFlow


def test_strategic_flow_initialization_and_state():
    """Verify StrategicFlow and StrategicFlowState instantiate correctly."""
    flow = StrategicIntelligenceFlow()
    assert flow is not None

    state = StrategicFlowState(crawl_run_id="crawl-a", language="ar")
    assert state.crawl_run_id == "crawl-a"
    assert state.execution_status == "pending"
    assert state.current_stage == "initialized"
    assert state.flow_id.startswith("flow-strat-")
