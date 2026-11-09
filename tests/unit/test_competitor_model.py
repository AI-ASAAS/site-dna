"""Model selection and verification tests for Phase 08."""

from site_dna.agents.competitor_intelligence_agent import create_competitor_intelligence_agent
from site_dna.core.config import Settings


def test_competitor_model_is_strictly_gemini_3_6_flash():
    settings = Settings(
        app_name="Test",
        app_env="test",
        gemini_api_key="dummy_key_12345",
    )

    # Core config verification
    assert settings.competitor_analysis_model == "gemini-3.6-flash"
    assert settings.get_effective_competitor_model() == "gemini-3.6-flash"

    # Agent identifier verification
    agent = create_competitor_intelligence_agent(settings=settings)
    assert agent.llm is not None
    # Model name in CrewAI is gemini/gemini-3.6-flash
    model_str = str(getattr(agent.llm, "model", getattr(agent.llm, "model_name", "")))
    assert "gemini-3.6-flash" in model_str
