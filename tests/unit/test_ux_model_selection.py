"""Unit test verifying that Gemini 3.6 Flash is the strictly configured model for Phase 05."""

from site_dna.agents.ux_ui_agent import create_ux_ui_agent
from site_dna.analysis.ux_ui.multimodal_adapter import UXMultimodalAdapter
from site_dna.core.config import get_settings


def test_ux_official_model_is_gemini_36_flash():
    """Verify that settings, agents, and multimodal adapters strictly target Gemini 3.6 Flash."""
    settings = get_settings()

    # 1. Configuration check
    assert settings.ux_analysis_model == "gemini-3.6-flash"
    assert settings.gemini_model == "gemini-3.6-flash"
    assert settings.visual_analysis_model == "gemini-3.6-flash"

    # 2. CrewAI Agent LLM target check
    agent = create_ux_ui_agent(settings=settings)
    assert agent.llm is not None
    assert "gemini-3.6-flash" in str(agent.llm.model)
    assert "gemini-3.8-flash" not in str(agent.llm.model)

    # 3. Multimodal Adapter model check
    adapter = UXMultimodalAdapter(settings=settings)
    assert adapter.settings.ux_analysis_model == "gemini-3.6-flash"
