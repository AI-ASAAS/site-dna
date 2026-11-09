"""Unit tests for Third-Party Resource Analyzer in Site DNA Phase 09."""

from site_dna.analysis.security_privacy.third_party_resources import ThirdPartyResourceAnalyzer
from site_dna.schemas.security_privacy import SecurityPageRecord


def test_third_party_resource_categorization():
    """Verify that external origins are correctly mapped into analytics, ads, cdn, and fonts."""
    analyzer = ThirdPartyResourceAnalyzer()

    page = SecurityPageRecord(
        page_url="https://example.com/",
        scheme="https",
        status_code=200,
        third_party_origins=[
            "https://www.google-analytics.com/g/collect",
            "https://connect.facebook.net/en_US/fbevents.js",
            "https://fonts.googleapis.com/css2",
            "https://cdnjs.cloudflare.com/ajax/libs/react/18.0.0/react.min.js",
            "https://custom-partner.example.org/api",
        ],
    )

    assessment = analyzer.analyze([page])

    assert assessment.unique_third_party_origins == 5
    assert assessment.has_analytics is True
    assert assessment.has_trackers is True
    assert len(assessment.third_party_origins_list) == 5

    analytics_rec = next(r for r in assessment.third_party_origins_list if "google-analytics.com" in r.origin)
    assert analytics_rec.resource_category == "analytics"
    assert analytics_rec.requires_privacy_review is True

    font_rec = next(r for r in assessment.third_party_origins_list if "fonts.googleapis.com" in r.origin)
    assert font_rec.resource_category == "fonts"
    assert font_rec.requires_privacy_review is False


def test_third_party_empty_origins():
    """Verify clean zero count when no external origins are observed."""
    analyzer = ThirdPartyResourceAnalyzer()
    page = SecurityPageRecord(
        page_url="https://local.example.com/",
        scheme="https",
        status_code=200,
        third_party_origins=[],
    )
    assessment = analyzer.analyze([page])
    assert assessment.unique_third_party_origins == 0
    assert len(assessment.third_party_origins_list) == 0
