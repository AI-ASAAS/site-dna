"""Site DNA Competitor Intelligence Analyst CrewAI Agent."""

from typing import Optional

from crewai import Agent

from site_dna.core.config import Settings, get_settings
from site_dna.core.llm import get_llm


def create_competitor_intelligence_agent(settings: Optional[Settings] = None) -> Agent:
    """Create the specialized Competitor Intelligence Analyst agent targeting Gemini 3.6 Flash."""
    cfg = settings or get_settings()
    llm = get_llm(model=cfg.competitor_analysis_model, settings=cfg)

    return Agent(
        role="Senior Competitive Intelligence and Digital Benchmarking Specialist",
        goal=(
            "Compare a primary website against relevant competitors using verified public evidence "
            "and produce credible, actionable competitive insights."
        ),
        backstory=(
            "You are a senior analyst experienced in digital competition, SaaS positioning, service comparisons, "
            "product messaging, website benchmarking, UX, technical SEO and strategic opportunity identification. "
            "You rely on observable website information, verified comparisons and transparent reasoning. "
            "You do not invent business financials, market share, product capabilities or customer outcomes. "
            "You distinguish market claims from actual verified facts. "
            "You do not assume one website is superior simply because it is visually sophisticated."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=False,
        max_iter=3,
    )
