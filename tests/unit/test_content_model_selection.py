"""Unit tests verifying official AI model selection for Content & Marketing Intelligence."""

from site_dna.agents.content_marketing_agent import create_content_marketing_agent
from site_dna.core.config import Settings


def test_content_official_model_is_gemini_36_flash():
    """Verify that Content & Marketing Analyst strictly targets Gemini 3.6 Flash."""
    settings = Settings(
        gemini_model="gemini-3.6-flash",
        content_analysis_model="gemini-3.6-flash",
        gemini_api_key="AQ.test-content-key-12345",
    )

    assert settings.content_analysis_model == "gemini-3.6-flash"
    assert settings.gemini_model == "gemini-3.6-flash"

    # Agent verification
    agent = create_content_marketing_agent(settings=settings)
    assert agent is not None
    assert "gemini-3.6-flash" in str(agent.llm.model)
