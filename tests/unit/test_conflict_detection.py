"""Unit tests for Phase 11 Conflict & Trade-off Detection."""

from site_dna.analysis.strategic_intelligence.conflict_detection import ConflictDetector
from site_dna.schemas.strategic_intelligence import UnifiedFinding


def test_conflict_detection_performance_vs_rich_visuals():
    """Verify conflict detection when visual identity recommends high-res media while SEO/perf demands reduction."""
    detector = ConflictDetector()

    f_perf = UnifiedFinding(
        unified_finding_id="uf-perf-1",
        source_phase="technical_seo",
        source_agent="Technical SEO Analyst",
        source_finding_id="seo-lcp",
        source_run_id="run-1",
        primary_site_id="https://example.com",
        category="performance",
        title="Excessive video banner causing large payload and slow LCP",
        description="Heavy auto-playing video increases initial page load by 8MB",
        original_severity="high",
    )

    f_vis = UnifiedFinding(
        unified_finding_id="uf-vis-1",
        source_phase="visual_identity",
        source_agent="Visual Identity Analyst",
        source_finding_id="vis-video",
        source_run_id="run-1",
        primary_site_id="https://example.com",
        category="branding",
        title="Hero video reinforces modern brand storytelling",
        description="High-definition video background delivers engaging brand atmosphere",
        original_severity="medium",
    )

    conflicts = detector.detect_conflicts([f_perf, f_vis])
    assert len(conflicts) >= 1
    c = conflicts[0]
    assert c.conflict_type == "performance_vs_visual"
    assert c.proposed_resolution != ""
    assert c.proposed_resolution_ar != ""


def test_conflict_detection_security_vs_functionality():
    """Verify conflict detection when strict CSP blocks required tracking or scripts."""
    detector = ConflictDetector()

    f_sec = UnifiedFinding(
        unified_finding_id="uf-sec-csp",
        source_phase="security_privacy",
        source_agent="Security Analyst",
        source_finding_id="sec-csp",
        source_run_id="run-1",
        primary_site_id="https://example.com",
        category="security",
        title="Restrictive CSP without unsafe-inline",
        description="Content-Security-Policy should forbid inline scripts and third-party origins",
        original_severity="high",
    )

    f_cnt = UnifiedFinding(
        unified_finding_id="uf-cnt-script",
        source_phase="content_marketing",
        source_agent="Content Analyst",
        source_finding_id="cnt-track",
        source_run_id="run-1",
        primary_site_id="https://example.com",
        category="marketing",
        title="Third-party marketing analytics script required for campaign tracking",
        description="Inject marketing pixel script directly in header for conversion measurement",
        original_severity="medium",
    )

    conflicts = detector.detect_conflicts([f_sec, f_cnt])
    assert len(conflicts) >= 1
