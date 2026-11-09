"""Unit tests for CompetitorContextBuilder (Phase 08)."""

import pytest
from fastapi import HTTPException

from site_dna.analysis.competitor_intelligence.context_builder import CompetitorContextBuilder
from site_dna.core.config import Settings
from site_dna.schemas.competitor_intelligence import CompetitorAnalysisRequest


def test_competitor_context_builder_basic():
    settings = Settings(app_name="Test", app_env="test")
    builder = CompetitorContextBuilder(settings=settings)

    req = CompetitorAnalysisRequest(
        primary_url="https://primary.example.com",
        competitor_urls=["https://rival1.example.com", "https://rival2.example.com/pricing"],
    )

    ctx = builder.build_context(req)

    assert ctx.primary_site.url.rstrip("/") == "https://primary.example.com"
    assert ctx.primary_site.canonical_origin == "https://primary.example.com"
    assert len(ctx.competitor_sites) == 2
    assert ctx.competitor_sites[0].canonical_origin == "https://rival1.example.com"
    assert ctx.competitor_sites[1].canonical_origin == "https://rival2.example.com"


def test_competitor_context_builder_deduplication():
    settings = Settings(app_name="Test", app_env="test")
    builder = CompetitorContextBuilder(settings=settings)

    # Competitor list includes primary site and duplicate competitors
    req = CompetitorAnalysisRequest(
        primary_url="https://primary.example.com",
        competitor_urls=[
            "https://primary.example.com/about",  # should be excluded (same origin as primary)
            "https://rival1.example.com/page1",
            "https://rival1.example.com/page2",  # duplicate origin
        ],
    )

    ctx = builder.build_context(req)
    assert len(ctx.competitor_sites) == 1
    assert ctx.competitor_sites[0].canonical_origin == "https://rival1.example.com"


def test_competitor_context_builder_max_limits():
    settings = Settings(
        app_name="Test",
        app_env="test",
        competitor_analysis_max_competitors=2,
        competitor_analysis_hard_max_competitors=3,
    )
    builder = CompetitorContextBuilder(settings=settings)

    req = CompetitorAnalysisRequest(
        primary_url="https://primary.example.com",
        competitor_urls=[
            "https://c1.example.com",
            "https://c2.example.com",
            "https://c3.example.com",
            "https://c4.example.com",
        ],
    )

    ctx = builder.build_context(req)
    # Bounded to hard cap
    assert len(ctx.competitor_sites) <= 3


def test_competitor_context_builder_invalid_url():
    settings = Settings(app_name="Test", app_env="test")
    builder = CompetitorContextBuilder(settings=settings)

    with pytest.raises((ValueError, HTTPException)):
        builder.build_context(CompetitorAnalysisRequest(primary_url="ftp://invalid.com"))
