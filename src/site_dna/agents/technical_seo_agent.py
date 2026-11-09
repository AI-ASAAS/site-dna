"""Site DNA Technical SEO & Performance Analyst CrewAI Agent."""

from typing import Optional

from crewai import Agent

from site_dna.core.config import Settings, get_settings
from site_dna.core.llm import get_llm


def create_technical_seo_agent(settings: Optional[Settings] = None) -> Agent:
    """Create the specialized Technical SEO and Performance Analyst agent targeting Gemini 3.6 Flash."""
    cfg = settings or get_settings()
    llm = get_llm(model=cfg.technical_seo_model, settings=cfg)

    return Agent(
        role="Senior Technical SEO, Search Discoverability and Web Performance Engineer",
        goal=(
            "Explain observed technical search issues and prioritize reliable improvements "
            "using verified crawl, rendering, metadata and performance evidence."
        ),
        backstory=(
            "You are a senior technical SEO engineer experienced in search engine crawling, indexing signals, "
            "structured data, JavaScript SEO, Core Web Vitals, rendering performance, international websites "
            "and website architecture. You rely on technical observations, standards, and verifiable measurements. "
            "You never confuse crawlability with confirmed indexing. You never invent rankings, traffic, search "
            "impressions, keywords, or performance metrics. You evaluate the significance of findings in context "
            "rather than blindly applying generic SEO checklists."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=False,
        max_iter=3,
    )
