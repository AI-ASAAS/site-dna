"""Unit tests for Mixed Content Analyzer in Site DNA Phase 09."""

from site_dna.analysis.security_privacy.mixed_content import MixedContentAnalyzer
from site_dna.schemas.security_privacy import SecurityPageRecord


def test_mixed_content_detection_and_classification():
    """Verify detection and query parameter stripping of mixed content resources."""
    analyzer = MixedContentAnalyzer()

    page = SecurityPageRecord(
        page_url="https://secure.example.com/dashboard",
        scheme="https",
        status_code=200,
        mixed_content_resources=[
            "http://insecure.example.com/app.js?token=secret123",
            "http://cdn.example.org/styles.css",
            "http://media.example.com/banner.png?user_id=987",
        ],
    )

    assessment = analyzer.analyze([page])

    assert assessment.has_mixed_content is True
    assert assessment.insecure_references_count == 3
    assert len(assessment.records) == 3

    # Verify query params were stripped from resource URLs
    for rec in assessment.records:
        assert "?" not in rec.insecure_resource_url
        assert "token=secret123" not in rec.insecure_resource_url
        assert "user_id=987" not in rec.insecure_resource_url

    script_rec = next(r for r in assessment.records if r.insecure_resource_url.endswith("app.js"))
    assert script_rec.resource_type == "script"

    img_rec = next(r for r in assessment.records if r.insecure_resource_url.endswith("banner.png"))
    assert img_rec.resource_type == "image"


def test_mixed_content_clean_page():
    """Verify that pure HTTPS pages report zero mixed content."""
    analyzer = MixedContentAnalyzer()

    page = SecurityPageRecord(
        page_url="https://secure.example.com/",
        scheme="https",
        status_code=200,
        mixed_content_resources=[],
    )

    assessment = analyzer.analyze([page])
    assert assessment.has_mixed_content is False
    assert assessment.insecure_references_count == 0
    assert len(assessment.records) == 0
