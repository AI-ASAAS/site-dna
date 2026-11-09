"""Unit tests for Phase 11 Root Causes and Strategic Opportunities."""

from site_dna.analysis.strategic_intelligence.opportunity_synthesis import OpportunitySynthesizer
from site_dna.analysis.strategic_intelligence.root_cause_candidates import RootCauseAnalyzer
from site_dna.schemas.strategic_intelligence import UnifiedFinding


def test_root_cause_does_not_claim_private_code_access():
    """Verify synthesized root causes are marked as external observation hypotheses."""
    analyzer = RootCauseAnalyzer()

    findings = [
        UnifiedFinding(
            unified_finding_id="uf-1",
            source_phase="accessibility",
            source_agent="Accessibility Analyst",
            source_finding_id="a11y-f1",
            source_run_id="run-1",
            primary_site_id="https://example.com",
            category="forms",
            title="Missing label on email input field",
            description="Input lacks associated label element",
            original_severity="medium",
            page_url="https://example.com/login",
        ),
        UnifiedFinding(
            unified_finding_id="uf-2",
            source_phase="accessibility",
            source_agent="Accessibility Analyst",
            source_finding_id="a11y-f2",
            source_run_id="run-1",
            primary_site_id="https://example.com",
            category="forms",
            title="Missing label on password input field",
            description="Password input field has no label or aria-label",
            original_severity="medium",
            page_url="https://example.com/signup",
        ),
    ]

    root_causes = analyzer.analyze_root_causes(findings)
    assert len(root_causes) >= 1
    for rc in root_causes:
        # Must clearly state observational hypothesis nature
        assert "hypothesis" in rc.title.lower() or "candidate" in rc.title.lower() or "component" in rc.title.lower()
        assert rc.shared_pattern != ""
        assert rc.description != ""


def test_opportunities_zero_financial_roi_hallucination():
    """Verify that synthesized opportunities NEVER claim ungrounded revenue percentages or monetary sums."""
    synthesizer = OpportunitySynthesizer()

    findings = [
        UnifiedFinding(
            unified_finding_id="uf-1",
            source_phase="accessibility",
            source_agent="Accessibility Analyst",
            source_finding_id="a11y-1",
            source_run_id="run-1",
            primary_site_id="https://example.com",
            category="forms",
            title="Form input missing accessible label",
            description="Contact form inputs lack associated label elements",
            original_severity="high",
            page_url="https://example.com/contact",
        )
    ]

    opportunities = synthesizer.synthesize_opportunities(findings)
    assert len(opportunities) >= 1
    for opp in opportunities:
        benefit = opp.expected_type_of_benefit.lower()
        assert "$" not in benefit
        assert "revenue increase" not in benefit
