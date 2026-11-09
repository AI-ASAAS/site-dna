"""Unit tests for InteractionAnalyzer (CTA discovery, small touch targets, unlabeled controls)."""

from pathlib import Path

from site_dna.analysis.ux_ui.context_builder import UXContextBuilder
from site_dna.analysis.ux_ui.interaction_analyzer import InteractionAnalyzer

FIXTURES_DIR = Path("tests/fixtures/ux_ui")


def test_interaction_analyzer_fixture_a_good_ctas():
    """Verify proper CTA detection and touch target compliance on Fixture A."""
    base_dir = FIXTURES_DIR / "fixture_a_good_ux" / "runs"
    builder = UXContextBuilder(base_dir=str(base_dir))
    context = builder.build_context(visual_run_id="vis-a", crawl_run_id="crawl-a")

    assessment = InteractionAnalyzer.analyze_interactions(context.pages, context.evidence_index)

    assert assessment.total_buttons > 0
    assert len(assessment.cta_candidates) > 0
    assert len(assessment.small_touch_targets) == 0


def test_interaction_analyzer_fixture_c_undersized_targets():
    """Verify detection of undersized interactive targets on Fixture C."""
    base_dir = FIXTURES_DIR / "fixture_c_mobile_problems" / "runs"
    builder = UXContextBuilder(base_dir=str(base_dir))
    context = builder.build_context(visual_run_id="vis-c", crawl_run_id="crawl-c")

    assessment = InteractionAnalyzer.analyze_interactions(context.pages, context.evidence_index)

    assert len(assessment.small_touch_targets) > 0
    # Must generate a finding for the tiny button
    findings = [f for f in assessment.findings if "المس" in f.title or "interaction" in f.category]
    assert len(findings) > 0
