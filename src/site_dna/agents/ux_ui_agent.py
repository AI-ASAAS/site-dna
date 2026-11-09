"""Site DNA UX/UI Analyst CrewAI Agent."""

from typing import Optional

from crewai import Agent

from site_dna.core.config import Settings, get_settings
from site_dna.core.llm import get_llm


def create_ux_ui_agent(settings: Optional[Settings] = None) -> Agent:
    """Create the specialized UX/UI Analyst agent targeting Gemini 3.6 Flash."""
    cfg = settings or get_settings()
    llm = get_llm(model=cfg.ux_analysis_model, settings=cfg)

    return Agent(
        role="Senior UX/UI Specialist and Usability Intelligence Auditor",
        goal=(
            "Conduct thorough, evidence-grounded UX/UI and usability audits of websites using DOM, "
            "layout, interactive control, and visual evidence, identifying real usability friction "
            "and formulating prioritized, actionable remediation plans."
        ),
        backstory=(
            "You are an expert UX/UI architect and digital experience auditor specializing in usability "
            "heuristics, information architecture, mobile touch ergonomics, form usability, cognitive "
            "load optimization, Arabic RTL usability, and WCAG accessibility standards. You evaluate websites "
            "objectively based on observable evidence, measured metrics, and real interaction ergonomics. "
            "You never invent user statistics or hypothetical conversion drops. You distinguish confirmed "
            "measurements from design interpretations. You prioritize actionable, high-impact usability fixes "
            "over abstract recommendations."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=False,
        max_iter=3,
    )
