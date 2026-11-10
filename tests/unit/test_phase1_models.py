"""Phase 1 contract tests for report models and shared result types."""

import json

from site_dna.models.common import (
    CheckStatus,
    FileRef,
    ModuleError,
    ModuleResult,
    ModuleStatus,
)
from site_dna.models.page import PageData
from site_dna.models.performance import Performance, StrategyPerformance
from site_dna.models.report import Report
from site_dna.models.seo import SeoAnalysis
from site_dna.models.visual import VisualIdentity
from site_dna.scan import build_placeholder_report


def test_module_result_defaults() -> None:
    result = ModuleResult[dict](status=ModuleStatus.skipped, duration_ms=0)

    assert result.status is ModuleStatus.skipped
    assert result.data is None
    assert result.reason is None
    assert result.warnings == []
    assert result.errors == []


def test_module_result_serializes_generic_payload() -> None:
    result = ModuleResult[dict](
        status=ModuleStatus.ok,
        duration_ms=12,
        data={"value": 1},
        warnings=["w"],
        errors=[ModuleError(code="x", message="boom")],
    )

    dumped = result.model_dump()

    assert dumped["status"] == "ok"
    assert dumped["data"] == {"value": 1}
    assert dumped["errors"][0]["code"] == "x"


def test_file_ref_optional_dimensions_default_to_none() -> None:
    ref = FileRef(path="a.png", format="png", bytes=10, sha256="a" * 64)

    assert ref.width is None
    assert ref.height is None


def test_check_status_enum_values() -> None:
    assert {status.value for status in CheckStatus} == {
        "passed",
        "warning",
        "failed",
        "not_available",
    }


def test_page_data_requires_url_and_defaults_collections() -> None:
    page = PageData(url="https://example.com")

    assert page.url == "https://example.com"
    assert page.headings.h1 == []
    assert page.heading_outline == []
    assert page.links == []
    assert page.images == []
    assert page.markdown is None
    assert page.markdown_file is None


def test_strategy_performance_requires_status() -> None:
    strategy = StrategyPerformance(status=ModuleStatus.not_available, reason="missing_api_key")

    assert strategy.score is None
    assert strategy.lab.lcp_ms is None
    assert strategy.field.inp is None
    assert strategy.opportunities == []


def test_visual_and_seo_models_have_safe_defaults() -> None:
    visual = VisualIdentity()
    seo = SeoAnalysis()

    assert visual.colors.all == []
    assert visual.typography.font_families == []
    assert visual.screenshot is None
    assert visual.sampled_elements == 0
    assert seo.checks == []
    assert seo.issues == []
    assert seo.summary.failed == 0


def test_placeholder_report_is_schema_valid_and_all_modules_skipped() -> None:
    report = build_placeholder_report(
        scan_id="abc123",
        input_url="https://example.com",
        config={"max_pages": 20},
        tool_version="0.1.0",
    )

    payload = json.loads(report.model_dump_json())
    parsed = Report.model_validate(payload)

    assert parsed.schema_version == "1.0"
    assert parsed.scan_id == "abc123"
    assert parsed.project_info.permission_attested is True
    assert parsed.website_content.status is ModuleStatus.skipped
    assert parsed.visual_identity.status is ModuleStatus.skipped
    assert parsed.performance.status is ModuleStatus.skipped
    assert parsed.seo_analysis.status is ModuleStatus.skipped


def test_performance_wraps_both_strategies() -> None:
    performance = Performance(
        mobile=StrategyPerformance(status=ModuleStatus.skipped),
        desktop=StrategyPerformance(status=ModuleStatus.skipped),
    )

    assert performance.mobile.status is ModuleStatus.skipped
    assert performance.desktop.status is ModuleStatus.skipped
