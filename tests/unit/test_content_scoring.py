"""Unit tests for ContentScoringEngine."""

from pathlib import Path

from site_dna.analysis.content_marketing.context_builder import ContentContextBuilder
from site_dna.analysis.content_marketing.scoring import ContentScoringEngine
from site_dna.schemas.content_marketing import ContentFinding

FIXTURES_DIR = Path("tests/fixtures/content_marketing")


def test_content_scoring_no_findings():
    """Verify that a site with zero findings receives a 100/100 score."""
    base_dir = FIXTURES_DIR / "fixture_a_clear_messaging" / "runs"
    builder = ContentContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-a")

    overall, scores = ContentScoringEngine.calculate_scores([], pages)

    assert overall == 100.0
    assert len(scores) == 7
    total_weights = sum(s.weight for s in scores)
    assert abs(total_weights - 1.0) < 0.001


def test_content_scoring_deductions():
    """Verify that severity-based deductions properly lower the overall score."""
    base_dir = FIXTURES_DIR / "fixture_a_clear_messaging" / "runs"
    builder = ContentContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-a")

    findings = [
        ContentFinding(
            finding_id="F-1",
            title="Critical value prop error",
            category="value_proposition",
            description="desc",
            page_url=pages[0].page_url,
            severity="critical",
        )
    ]

    overall, scores = ContentScoringEngine.calculate_scores(findings, pages)

    assert overall < 100.0
    vp_score = next(s for s in scores if s.dimension_name == "value_proposition")
    assert vp_score.score == 75.0  # 100 - 25
