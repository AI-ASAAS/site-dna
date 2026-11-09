"""Unit tests for ContentEvidenceValidator."""

from pathlib import Path

from site_dna.analysis.content_marketing.context_builder import ContentContextBuilder
from site_dna.analysis.content_marketing.evidence_validator import ContentEvidenceValidator
from site_dna.schemas.content_marketing import ContentFinding

FIXTURES_DIR = Path("tests/fixtures/content_marketing")


def test_evidence_validator_valid_and_quarantine():
    """Verify that hallucinated URLs and fake text excerpts are quarantined."""
    base_dir = FIXTURES_DIR / "fixture_a_clear_messaging" / "runs"
    builder = ContentContextBuilder(base_dir=str(base_dir))
    pages, ev_index, _, _ = builder.build_context(crawl_run_id="crawl-a")

    findings = [
        # Valid finding
        ContentFinding(
            finding_id="F-VALID",
            title="Valid finding",
            category="messaging_clarity",
            description="desc",
            page_url=pages[0].page_url,
            source_excerpt="إدارة المشروعات",
        ),
        # Fake URL finding
        ContentFinding(
            finding_id="F-FAKE-URL",
            title="Fake URL finding",
            category="messaging_clarity",
            description="desc",
            page_url="https://totally-fake-url.example.com/",
        ),
        # Fake excerpt finding
        ContentFinding(
            finding_id="F-FAKE-EXCERPT",
            title="Fake excerpt finding",
            category="messaging_clarity",
            description="desc",
            page_url=pages[0].page_url,
            source_excerpt="This string definitely does not exist anywhere in Arabic copy XYZ123",
        ),
    ]

    valid, quarantined = ContentEvidenceValidator.validate_findings(findings, pages, ev_index)

    assert len(valid) == 1
    assert valid[0].finding_id == "F-VALID"
    assert len(quarantined) == 2
    quarantined_ids = {q.finding_id for q in quarantined}
    assert "F-FAKE-URL" in quarantined_ids
    assert "F-FAKE-EXCERPT" in quarantined_ids
