"""Unit tests verifying strict official model binding for Phase 11 Strategic Intelligence."""

from site_dna.agents.strategic_intelligence_agent import StrategicIntelligenceAgent
from site_dna.core.config import get_settings
from site_dna.tools.strategic_intelligence_tool import StrategicIntelligenceTool


def test_strategic_agent_strict_model_id():
    """Ensure Phase 11 Agent strictly binds to official Gemini 3.6 Flash."""
    agent = StrategicIntelligenceAgent()
    assert agent.MODEL_ID == "gemini/gemini-3.6-flash"
    assert "gemini-3.6-flash" in agent.MODEL_ID


def test_strategic_config_effective_model():
    """Ensure Settings config strictly defaults to gemini-3.6-flash."""
    settings = get_settings()
    model = settings.get_effective_strategic_model()
    assert model == "gemini-3.6-flash"


def test_strategic_agent_instantiation():
    """Verify CrewAI Agent creation with strategic persona and goal."""
    agent_inst = StrategicIntelligenceAgent()
    crew_agent = agent_inst.get_agent()
    assert crew_agent is not None
    assert crew_agent.role is not None
    assert "Strategist" in crew_agent.role or "Synthesis" in crew_agent.role
    assert crew_agent.goal is not None


def test_strategic_tool_initialization():
    """Verify StrategicIntelligenceTool metadata and parameters."""
    tool = StrategicIntelligenceTool()
    assert tool.name == "strategic_intelligence_tool"
    assert "multi-agent" in tool.description.lower() or "artifacts" in tool.description.lower()
