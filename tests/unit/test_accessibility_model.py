"""Unit tests verifying strict model binding for Phase 10 Accessibility Agent."""

from site_dna.agents.accessibility_agent import AccessibilityAgent
from site_dna.core.config import get_settings


def test_accessibility_agent_strict_model_id():
    agent = AccessibilityAgent()
    assert agent.MODEL_ID == "gemini/gemini-3.6-flash"
    assert "gemini-3.6-flash" in agent.MODEL_ID


def test_accessibility_config_effective_model():
    settings = get_settings()
    model = settings.get_effective_accessibility_model()
    assert model == "gemini-3.6-flash"


def test_accessibility_agent_instantiation():
    agent_inst = AccessibilityAgent()
    crew_agent = agent_inst.get_agent()
    assert crew_agent is not None
    assert crew_agent.role is not None
    assert "WCAG" in crew_agent.role or "Accessibility" in crew_agent.role
