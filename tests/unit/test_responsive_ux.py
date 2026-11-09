"""Unit tests for ResponsiveAnalyzer (horizontal overflow, clipped elements, mobile navigation)."""

from pathlib import Path

from site_dna.analysis.ux_ui.context_builder import UXContextBuilder
from site_dna.analysis.ux_ui.responsive_analyzer import ResponsiveAnalyzer

FIXTURES_DIR = Path("tests/fixtures/ux_ui")


def test_responsive_analyzer_fixture_a_no_overflow():
    """Verify absence of horizontal overflow on clean Fixture A."""
    base_dir = FIXTURES_DIR / "fixture_a_good_ux" / "runs"
    builder = UXContextBuilder(base_dir=str(base_dir))
    context = builder.build_context(visual_run_id="vis-a", crawl_run_id="crawl-a")

    assessment = ResponsiveAnalyzer.analyze_responsive(context.pages, context.evidence_index)

    assert not assessment.horizontal_overflow_detected
    assert len(assessment.overflow_pages) == 0
    assert assessment.clipped_elements_count == 0


def test_responsive_analyzer_fixture_c_overflow_and_clipping():
    """Verify detection of horizontal overflow and clipped elements on Fixture C."""
    base_dir = FIXTURES_DIR / "fixture_c_mobile_problems" / "runs"
    builder = UXContextBuilder(base_dir=str(base_dir))
    context = builder.build_context(visual_run_id="vis-c", crawl_run_id="crawl-c")

    assessment = ResponsiveAnalyzer.analyze_responsive(context.pages, context.evidence_index)

    assert assessment.horizontal_overflow_detected
    assert assessment.clipped_elements_count > 0
    assert len(assessment.findings) > 0
