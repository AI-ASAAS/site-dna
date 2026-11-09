"""Unit tests for FeatureMatrixBuilder (Phase 08)."""

from site_dna.analysis.competitor_intelligence.feature_comparison import FeatureMatrixBuilder
from tests.fixtures.competitor_intelligence.test_fixtures import (
    COMPETITOR_1_CRAWL_DATA,
    PRIMARY_CRAWL_DATA,
    make_sample_context,
)


def test_feature_matrix_builder_provenance_statuses():
    ctx = make_sample_context()
    builder = FeatureMatrixBuilder()

    crawl_dataset = {
        ctx.primary_site.site_id: PRIMARY_CRAWL_DATA,
        ctx.competitor_sites[0].site_id: COMPETITOR_1_CRAWL_DATA,
    }

    matrix = builder.build_matrix(
        primary_site=ctx.primary_site,
        competitor_sites=ctx.competitor_sites,
        crawl_dataset=crawl_dataset,
    )

    assert len(matrix) > 0
    valid_statuses = {
        "observed_present",
        "observed_absent_in_inspected_scope",
        "claimed",
        "not_found_in_sample",
        "not_assessed",
        "not_comparable",
    }

    for record in matrix:
        assert record.feature_name is not None
        assert record.primary_status in valid_statuses
        for comp_id, comp_info in record.competitor_statuses.items():
            assert comp_info["status"] in valid_statuses


def test_feature_matrix_detects_observed_present():
    ctx = make_sample_context()
    builder = FeatureMatrixBuilder()

    crawl_dataset = {
        ctx.primary_site.site_id: PRIMARY_CRAWL_DATA,
        ctx.competitor_sites[0].site_id: COMPETITOR_1_CRAWL_DATA,
    }

    matrix = builder.build_matrix(
        primary_site=ctx.primary_site,
        competitor_sites=ctx.competitor_sites,
        crawl_dataset=crawl_dataset,
    )

    # Primary CRM HTML mentions "API access", "webhooks", so api_access should be observed_present
    api_feat = next((f for f in matrix if f.feature_id == "api_access"), None)
    assert api_feat is not None
    assert api_feat.primary_status == "observed_present"
