"""Unit tests for NavigationAnalyzer (link graph, depth, orphan pages, ambiguous labels)."""

from pathlib import Path

from site_dna.analysis.ux_ui.context_builder import UXContextBuilder
from site_dna.analysis.ux_ui.navigation_analyzer import NavigationAnalyzer

FIXTURES_DIR = Path("tests/fixtures/ux_ui")


def test_navigation_analyzer_fixture_a_clean():
    """Verify clean navigation on Fixture A."""
    base_dir = FIXTURES_DIR / "fixture_a_good_ux" / "runs"
    builder = UXContextBuilder(base_dir=str(base_dir))
    context = builder.build_context(visual_run_id="vis-a", crawl_run_id="crawl-a")

    assessment = NavigationAnalyzer.analyze_navigation(context.pages, context.evidence_index)

    assert assessment.max_navigation_depth <= 2
    assert len(assessment.isolated_pages) == 0
    assert len(assessment.ambiguous_labels) == 0
    # Findings should have no critical issues
    criticals = [f for f in assessment.findings if f.severity == "critical"]
    assert len(criticals) == 0


def test_navigation_analyzer_fixture_b_anomalies():
    """Verify detection of orphan pages, deep hierarchy, and ambiguous labels on Fixture B."""
    base_dir = FIXTURES_DIR / "fixture_b_poor_navigation" / "runs"
    builder = UXContextBuilder(base_dir=str(base_dir))
    context = builder.build_context(visual_run_id="vis-b", crawl_run_id="crawl-b")

    assessment = NavigationAnalyzer.analyze_navigation(context.pages, context.evidence_index)

    # Should detect isolated/orphan page
    assert any("orphan" in p for p in assessment.isolated_pages) or len(assessment.isolated_pages) > 0

    # Should detect ambiguous links ("اضغط هنا", "المزيد")
    assert len(assessment.ambiguous_labels) > 0

    # Should detect duplicate links pointing to different destinations
    assert len(assessment.duplicate_labels) > 0

    # Findings should be present
    assert len(assessment.findings) > 0
