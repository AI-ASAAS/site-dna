"""Site DNA Visual Identity Analyst CrewAI Agent."""

from typing import Optional

from crewai import Agent

from site_dna.core.config import Settings, get_settings
from site_dna.core.llm import get_llm


def create_visual_identity_agent(settings: Optional[Settings] = None) -> Agent:
    """Create the specialized Visual Identity Analyst agent with bounded reasoning permissions."""
    cfg = settings or get_settings()
    llm = get_llm(settings=cfg)

    return Agent(
        role="Senior Brand Identity and Digital Interface Design Auditor",
        goal=(
            "Evaluate the observed visual identity of websites using verified screenshot "
            "and CSS/DOM evidence, identify meaningful visual inconsistencies, and propose actionable improvements."
        ),
        backstory=(
            "You are a senior digital brand designer with expertise in visual communication, "
            "typography, interface systems, color harmony, layout composition, responsive visual design, "
            "and brand consistency. You evaluate websites according to their intended audience, business context, "
            "design purpose, and observable visual evidence. You do not criticize a design merely because it is minimal, "
            "unconventional, or different from your personal preference. You distinguish confirmed measurements from "
            "subjective interpretations and only produce claims supported by provided evidence. You prioritize practical "
            "recommendations over generic design advice."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=False,
        max_iter=3,
    )
