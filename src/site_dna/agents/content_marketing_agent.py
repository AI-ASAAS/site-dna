"""Site DNA Content & Marketing Analyst CrewAI Agent."""

from typing import Optional

from crewai import Agent

from site_dna.core.config import Settings, get_settings
from site_dna.core.llm import get_llm


def create_content_marketing_agent(settings: Optional[Settings] = None) -> Agent:
    """Create the specialized Content & Marketing Analyst agent targeting Gemini 3.6 Flash."""
    cfg = settings or get_settings()
    llm = get_llm(model=cfg.content_analysis_model, settings=cfg)

    return Agent(
        role="Senior Website Messaging, Content Strategy and Conversion Copy Auditor",
        goal=(
            "Evaluate website messaging and content using verified source evidence, identify communication "
            "weaknesses, and propose grounded improvements."
        ),
        backstory=(
            "You are a senior digital content strategist specializing in value propositions, product messaging, "
            "service positioning, persuasive copywriting, brand voice, audience communication, and content "
            "architecture. You evaluate communication according to its context. You do not assume that longer content, "
            "stronger sales language, or more CTAs automatically means better content. You distinguish business facts "
            "from claims and recommendations. You do not invent product details or customer outcomes."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=False,
        max_iter=3,
    )
