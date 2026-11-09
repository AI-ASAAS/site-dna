"""Unit tests for Phase 11 Finding Normalizer."""

from site_dna.analysis.strategic_intelligence.finding_normalizer import FindingNormalizer


def test_normalize_raw_finding_generates_stable_id():
    """Verify that normalization produces deterministic sha256-based unified finding IDs."""
    normalizer = FindingNormalizer()
    raw_item = {
        "finding_id": "raw-1",
        "title": "Low contrast on CTA button",
        "description": "Button contrast ratio is 2.8:1 below required 4.5:1",
        "severity": "high",
        "confidence": 0.95,
        "evidence_ids": ["ev-1", "ev-2"],
        "page_url": "https://example.com/",
    }

    unified_1 = normalizer.normalize(
        source_phase="accessibility",
        source_agent="Accessibility Analyst",
        source_run_id="run-1",
        primary_site_id="https://example.com",
        raw_finding=raw_item,
    )
    unified_2 = normalizer.normalize(
        source_phase="accessibility",
        source_agent="Accessibility Analyst",
        source_run_id="run-1",
        primary_site_id="https://example.com",
        raw_finding=raw_item,
    )

    assert unified_1.unified_finding_id == unified_2.unified_finding_id
    assert unified_1.unified_finding_id.startswith("uf-")
    assert unified_1.source_agent == "Accessibility Analyst"
    assert unified_1.original_severity == "high"
    assert unified_1.evidence_ids == ["ev-1", "ev-2"]


def test_normalize_severity_mapping():
    """Verify mapping of diverse agent severities to normalized impact categories."""
    normalizer = FindingNormalizer()
    critical_item = {"finding_id": "sec-1", "title": "Missing SSL", "severity": "critical"}
    low_item = {"finding_id": "cnt-1", "title": "Minor typo", "severity": "low"}

    uf_crit = normalizer.normalize(
        source_phase="security_privacy",
        source_agent="Security Analyst",
        source_run_id="run-1",
        primary_site_id="https://example.com",
        raw_finding=critical_item,
    )
    uf_low = normalizer.normalize(
        source_phase="content_marketing",
        source_agent="Content Analyst",
        source_run_id="run-1",
        primary_site_id="https://example.com",
        raw_finding=low_item,
    )

    assert uf_crit.normalized_impact_category in ("critical_blocker", "high_friction")
    assert uf_low.normalized_impact_category in ("minor_friction", "minor_observation", "moderate_impairment")
