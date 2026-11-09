"""Unit tests for Phase 11 context builder and source registry."""

import pytest
from site_dna.analysis.strategic_intelligence.context_builder import StrategicContextBuilder
from site_dna.analysis.strategic_intelligence.source_registry import SUPPORTED_SOURCE_AGENTS
from site_dna.schemas.strategic_intelligence import StrategicAnalysisRequest


def test_source_registry_specs():
    """Verify registry catalogs all source phases 04 through 10."""
    expected_phases = {
        "visual_identity",
        "ux_ui",
        "content_marketing",
        "technical_seo",
        "competitor_intelligence",
        "security_privacy",
        "accessibility",
    }
    assert expected_phases.issubset(SUPPORTED_SOURCE_AGENTS.keys())

    a11y_spec = SUPPORTED_SOURCE_AGENTS["accessibility"]
    assert a11y_spec.phase_number == 10
    assert a11y_spec.artifact_subfolder == "accessibility"


def test_context_builder_path_traversal_protection():
    """Verify that path traversal in run IDs is strictly blocked."""
    builder = StrategicContextBuilder()
    with pytest.raises(ValueError):
        req = StrategicAnalysisRequest(crawl_run_id="../../../etc/passwd")
        builder.build_context(req)

    with pytest.raises(ValueError):
        req = StrategicAnalysisRequest(crawl_run_id="crawl-a; rm -rf /")
        builder.build_context(req)


def test_context_builder_ingests_real_run():
    """Verify context builder successfully parses crawl-a run artifacts."""
    builder = StrategicContextBuilder()
    req = StrategicAnalysisRequest(crawl_run_id="crawl-a")
    context = builder.build_context(req)
    assert context is not None
    assert context["crawl_run_id"] == "crawl-a"
    assert "coverage" in context
    assert len(context["coverage"].available_agents) > 0
