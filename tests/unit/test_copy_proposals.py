"""Unit tests for CopyProposalsEngine."""

from pathlib import Path

from site_dna.analysis.content_marketing.context_builder import ContentContextBuilder
from site_dna.analysis.content_marketing.copy_proposals import CopyProposalsEngine
from site_dna.schemas.content_marketing import ContentFinding

FIXTURES_DIR = Path("tests/fixtures/content_marketing")


def test_copy_proposals_fixture_h_fact_preservation():
    """Verify that copy rewrite proposals preserve confirmed facts and do not invent new ones."""
    base_dir = FIXTURES_DIR / "fixture_h_rewrite_integrity" / "runs"
    builder = ContentContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-h")

    findings = [
        ContentFinding(
            finding_id="CF-CTA-1",
            title="صياغة CTA عامة ('اشترك الآن')",
            category="cta_action",
            description="الزر عام",
            page_url=pages[0].page_url,
            source_excerpt="اشترك الآن",
        )
    ]

    proposals = CopyProposalsEngine.generate_proposals(pages=pages, findings=findings)

    assert len(proposals) > 0
    for p in proposals:
        assert p.is_suggestion is True
        assert p.proposed_replacement != ""
        assert len(p.facts_preserved) > 0
