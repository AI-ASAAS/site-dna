"""Unit tests for FormsAnalyzer (labels, placeholder-only fields, submit buttons)."""

from pathlib import Path

from site_dna.analysis.ux_ui.context_builder import UXContextBuilder
from site_dna.analysis.ux_ui.forms_analyzer import FormsAnalyzer

FIXTURES_DIR = Path("tests/fixtures/ux_ui")


def test_forms_analyzer_fixture_a_compliant():
    """Verify clean form analysis with explicit labels and submit buttons on Fixture A."""
    base_dir = FIXTURES_DIR / "fixture_a_good_ux" / "runs"
    builder = UXContextBuilder(base_dir=str(base_dir))
    context = builder.build_context(visual_run_id="vis-a", crawl_run_id="crawl-a")

    assessment = FormsAnalyzer.analyze_forms(context.pages, context.evidence_index)

    assert assessment.forms_detected == 2
    assert assessment.total_fields >= 4
    assert len(assessment.unlabeled_fields) == 0
    assert len(assessment.missing_submit_buttons) == 0


def test_forms_analyzer_fixture_d_defects():
    """Verify detection of unlabeled fields, placeholder-only fields, and missing submit on Fixture D."""
    base_dir = FIXTURES_DIR / "fixture_d_form_problems" / "runs"
    builder = UXContextBuilder(base_dir=str(base_dir))
    context = builder.build_context(visual_run_id="vis-d", crawl_run_id="crawl-d")

    assessment = FormsAnalyzer.analyze_forms(context.pages, context.evidence_index)

    assert assessment.forms_detected == 1
    assert len(assessment.placeholder_only_fields) > 0
    assert len(assessment.unlabeled_fields) > 0
    assert len(assessment.missing_submit_buttons) > 0
    assert len(assessment.findings) >= 2
