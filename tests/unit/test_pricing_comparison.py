"""Unit tests for PricingComparator (Phase 08)."""

from site_dna.analysis.competitor_intelligence.pricing_comparison import PricingComparator
from tests.fixtures.competitor_intelligence.test_fixtures import (
    COMPETITOR_1_CRAWL_DATA,
    PRIMARY_CRAWL_DATA,
    make_sample_context,
)


def test_pricing_comparator_safeguards():
    ctx = make_sample_context()
    comparator = PricingComparator()

    crawl_dataset = {
        ctx.primary_site.site_id: PRIMARY_CRAWL_DATA,
        ctx.competitor_sites[0].site_id: COMPETITOR_1_CRAWL_DATA,
    }

    pricing_records = comparator.compare_pricing(
        primary_site=ctx.primary_site,
        competitor_sites=ctx.competitor_sites,
        crawl_dataset=crawl_dataset,
    )

    assert len(pricing_records) > 0
    valid_comparabilities = {"comparable", "not_comparable", "contact_sales", "not_published"}

    for record in pricing_records:
        assert record.plan_name is not None
        assert record.comparability_status in valid_comparabilities

    # Contact sales plans or custom quotes must not claim direct comparable numeric equality
    contact_plans = [p for p in pricing_records if p.is_contact_sales]
    for cp in contact_plans:
        assert cp.comparability_status in ("not_comparable", "contact_sales")
