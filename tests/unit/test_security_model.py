"""Unit tests verifying strict model binding to Gemini 3.6 Flash for Site DNA Phase 09."""

from site_dna.agents.security_privacy_agent import create_security_privacy_agent
from site_dna.core.config import Settings


def test_security_model_configuration_default():
    """Verify that default settings strictly specify gemini-3.6-flash for Phase 09."""
    settings = Settings()
    assert settings.security_analysis_model == "gemini-3.6-flash"
    assert settings.get_effective_security_model() == "gemini-3.6-flash"


def test_security_agent_uses_gemini_36_flash():
    """Verify that SecurityPrivacyAgent instantiates with gemini-3.6-flash."""
    agent = create_security_privacy_agent()
    # CrewAI Agent llm model identifier check
    llm_str = str(agent.llm)
    assert "gemini-3.6-flash" in llm_str or "gemini/gemini-3.6-flash" in llm_str
    assert "gemini-3.8-flash" not in llm_str
    assert "gpt-4" not in llm_str
