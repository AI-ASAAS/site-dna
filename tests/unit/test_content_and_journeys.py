"""Unit tests for ContentUsabilityAnalyzer and JourneyAnalyzer."""

from pathlib import Path

from site_dna.analysis.ux_ui.content_usability import ContentUsabilityAnalyzer
from site_dna.analysis.ux_ui.context_builder import UXContextBuilder
from site_dna.analysis.ux_ui.journey_analyzer import JourneyAnalyzer

FIXTURES_DIR = Path("tests/fixtures/ux_ui")


def test_content_usability_fixture_a_arabic_rtl():
    """Verify Arabic RTL declaration and scannable paragraphs on Fixture A."""
    base_dir = FIXTURES_DIR / "fixture_a_good_ux" / "runs"
    builder = UXContextBuilder(base_dir=str(base_dir))
    context = builder.build_context(visual_run_id="vis-a", crawl_run_id="crawl-a")

    assessment = ContentUsabilityAnalyzer.analyze_content(context.pages, context.evidence_index)

    assert assessment.rtl_supported
    assert assessment.scanability_score >= 80.0
    assert assessment.heading_count >= 5


def test_content_usability_fixture_e_missing_rtl_wall_of_text():
    """Verify detection of missing dir=rtl and wall-of-text paragraphs on Fixture E."""
    base_dir = FIXTURES_DIR / "fixture_e_arabic_rtl" / "runs"
    builder = UXContextBuilder(base_dir=str(base_dir))
    context = builder.build_context(visual_run_id="vis-e", crawl_run_id="crawl-e")

    assessment = ContentUsabilityAnalyzer.analyze_content(context.pages, context.evidence_index)

    assert not assessment.rtl_supported
    assert assessment.average_paragraph_length >= 100
    assert len(assessment.findings) > 0


def test_journey_analyzer_fixture_a_contact_flow():
    """Verify user journey mapping for Contact / Support on Fixture A."""
    base_dir = FIXTURES_DIR / "fixture_a_good_ux" / "runs"
    builder = UXContextBuilder(base_dir=str(base_dir))
    context = builder.build_context(visual_run_id="vis-a", crawl_run_id="crawl-a")

    journeys = JourneyAnalyzer.analyze_journeys(context.pages, context.evidence_index)

    assert len(journeys) >= 1
    contact_jrn = next((j for j in journeys if "تواصل" in j.goal or "Contact" in j.goal), None)
    assert contact_jrn is not None
    assert contact_jrn.status in ("verified_route", "graph_derived")
