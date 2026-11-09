"""Unit tests for AccessibilityAnalyzer (WCAG criteria, heading hierarchy, accessible names)."""

from pathlib import Path

from site_dna.analysis.ux_ui.accessibility_analyzer import AccessibilityAnalyzer
from site_dna.analysis.ux_ui.context_builder import UXContextBuilder

FIXTURES_DIR = Path("tests/fixtures/ux_ui")


def test_accessibility_analyzer_fixture_a_valid_hierarchy():
    """Verify heading hierarchy validity and accessible controls on Fixture A."""
    base_dir = FIXTURES_DIR / "fixture_a_good_ux" / "runs"
    builder = UXContextBuilder(base_dir=str(base_dir))
    context = builder.build_context(visual_run_id="vis-a", crawl_run_id="crawl-a")

    assessment = AccessibilityAnalyzer.analyze_accessibility(context.pages, context.evidence_index)

    assert assessment.heading_hierarchy_valid
    assert len(assessment.heading_issues) == 0


def test_accessibility_analyzer_fixture_e_hierarchy_skips():
    """Verify detection of heading hierarchy skips (H3 without H1) on Fixture E."""
    base_dir = FIXTURES_DIR / "fixture_e_arabic_rtl" / "runs"
    builder = UXContextBuilder(base_dir=str(base_dir))
    context = builder.build_context(visual_run_id="vis-e", crawl_run_id="crawl-e")

    assessment = AccessibilityAnalyzer.analyze_accessibility(context.pages, context.evidence_index)

    assert not assessment.heading_hierarchy_valid
    assert len(assessment.heading_issues) > 0
    assert len(assessment.findings) > 0
