"""Unit tests for Phase 11 multi-agent deduplication with false-merge safeguards."""

from site_dna.analysis.strategic_intelligence.deduplication import FindingDeduplicator
from site_dna.schemas.strategic_intelligence import UnifiedFinding


def test_deduplication_detects_equivalent_cross_agent_findings():
    """Verify equivalent findings across SEO and Performance are grouped."""
    deduplicator = FindingDeduplicator()

    f1 = UnifiedFinding(
        unified_finding_id="uf-1",
        source_phase="technical_seo",
        source_agent="Technical SEO Analyst",
        source_finding_id="seo-img-1",
        source_run_id="run-1",
        primary_site_id="https://example.com",
        category="performance",
        title="Uncompressed hero images slowing LCP",
        description="Large uncompressed JPEG on homepage causes 4.2s LCP",
        page_url="https://example.com/",
        original_severity="high",
        evidence_ids=["ev-img"],
    )

    f2 = UnifiedFinding(
        unified_finding_id="uf-2",
        source_phase="ux_ui",
        source_agent="UX/UI Experience Analyst",
        source_finding_id="ux-img-2",
        source_run_id="run-1",
        primary_site_id="https://example.com",
        category="usability",
        title="Hero image unoptimized load delay",
        description="Hero banner takes excessive time to render on mobile",
        page_url="https://example.com/",
        original_severity="medium",
        evidence_ids=["ev-img"],
    )

    f3 = UnifiedFinding(
        unified_finding_id="uf-3",
        source_phase="security_privacy",
        source_agent="Security Analyst",
        source_finding_id="sec-hsts",
        source_run_id="run-1",
        primary_site_id="https://example.com",
        category="security",
        title="Missing HSTS Header",
        description="Strict-Transport-Security header not configured",
        original_severity="high",
    )

    deduped_findings, groups = deduplicator.deduplicate([f1, f2, f3])
    assert isinstance(groups, list)
    assert len(groups) >= 1
    grouped_finding_ids = [f.unified_finding_id for g in groups for f in g.findings]
    assert "uf-1" in grouped_finding_ids or "uf-2" in grouped_finding_ids


def test_deduplication_safeguards_against_false_merges():
    """Ensure distinct issues on different URLs or distinct topics are NOT merged."""
    deduplicator = FindingDeduplicator()

    f_contrast = UnifiedFinding(
        unified_finding_id="uf-c",
        source_phase="accessibility",
        source_agent="Accessibility Analyst",
        source_finding_id="a11y-c",
        source_run_id="run-1",
        primary_site_id="https://example.com",
        category="visual_accessibility",
        title="Color contrast failure on footer text",
        description="Contrast 2.1:1 fails WCAG AA",
        page_url="https://example.com/contact",
        original_severity="medium",
    )

    f_alt = UnifiedFinding(
        unified_finding_id="uf-a",
        source_phase="accessibility",
        source_agent="Accessibility Analyst",
        source_finding_id="a11y-a",
        source_run_id="run-1",
        primary_site_id="https://example.com",
        category="media",
        title="Missing alt attribute on logo",
        description="Image element missing text alternative",
        page_url="https://example.com/",
        original_severity="high",
    )

    deduped_findings, groups = deduplicator.deduplicate([f_contrast, f_alt])
    assert len(groups) == 0
