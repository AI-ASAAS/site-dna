"""Unit tests for CompetitorProfileExtractor and OfferingAnalyzer (Phase 08)."""

from site_dna.analysis.competitor_intelligence.company_profiles import CompetitorProfileExtractor
from site_dna.analysis.competitor_intelligence.offering_analyzer import OfferingAnalyzer
from site_dna.schemas.competitor_intelligence import CompetitorSourceRecord
from tests.fixtures.competitor_intelligence.test_fixtures import COMPETITOR_1_CRAWL_DATA, PRIMARY_CRAWL_DATA


def test_competitor_profile_extraction():
    extractor = CompetitorProfileExtractor()
    src = CompetitorSourceRecord(
        site_id="primary",
        url="https://primary-crm.example.com",
        canonical_origin="https://primary-crm.example.com",
        display_name="Primary CRM",
        role="primary",
    )

    profile = extractor.extract_profile(src, PRIMARY_CRAWL_DATA)

    assert profile.display_name is not None
    assert profile.site_id == "primary"
    assert len(profile.business_description) > 0


def test_offering_analyzer_normalization():
    analyzer = OfferingAnalyzer()
    src = CompetitorSourceRecord(
        site_id="comp_1",
        url="https://rival-crm.example.com",
        canonical_origin="https://rival-crm.example.com",
        display_name="Rival CRM",
        role="competitor",
    )
    offerings = analyzer.extract_offerings(src, COMPETITOR_1_CRAWL_DATA)

    assert len(offerings) > 0
    for o in offerings:
        assert o.name is not None
        assert o.category is not None
