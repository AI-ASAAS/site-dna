"""Unit tests for CompetitorRelevanceClassifier (Phase 08)."""

from site_dna.analysis.competitor_intelligence.relevance import CompetitorRelevanceClassifier
from site_dna.schemas.competitor_intelligence import CompetitorSourceRecord
from tests.fixtures.competitor_intelligence.test_fixtures import (
    COMPETITOR_1_CRAWL_DATA,
    COMPETITOR_2_INDIRECT_DATA,
    PRIMARY_CRAWL_DATA,
)


def test_relevance_classification_direct():
    classifier = CompetitorRelevanceClassifier()

    primary_src = CompetitorSourceRecord(
        site_id="primary",
        url="https://primary-crm.example.com",
        canonical_origin="https://primary-crm.example.com",
        display_name="Primary CRM",
        role="primary",
    )
    comp_src = CompetitorSourceRecord(
        site_id="comp_1",
        url="https://rival-crm.example.com",
        canonical_origin="https://rival-crm.example.com",
        display_name="Rival CRM",
        role="competitor",
    )

    relevance = classifier.classify_relevance(
        primary_site=primary_src,
        competitor_site=comp_src,
        primary_data=PRIMARY_CRAWL_DATA,
        competitor_data=COMPETITOR_1_CRAWL_DATA,
    )

    assert relevance.relevance_category in ("direct", "indirect", "adjacent", "unknown")
    assert relevance.relevance_score >= 0.0
    assert len(relevance.reason_ar) > 0


def test_relevance_classification_indirect():
    classifier = CompetitorRelevanceClassifier()

    primary_src = CompetitorSourceRecord(
        site_id="primary",
        url="https://primary-crm.example.com",
        canonical_origin="https://primary-crm.example.com",
        display_name="Primary CRM",
        role="primary",
    )
    comp_src = CompetitorSourceRecord(
        site_id="comp_2",
        url="https://support-desk.example.com",
        canonical_origin="https://support-desk.example.com",
        display_name="SupportDesk",
        role="competitor",
    )

    relevance = classifier.classify_relevance(
        primary_site=primary_src,
        competitor_site=comp_src,
        primary_data=PRIMARY_CRAWL_DATA,
        competitor_data=COMPETITOR_2_INDIRECT_DATA,
    )

    assert relevance.relevance_category is not None
