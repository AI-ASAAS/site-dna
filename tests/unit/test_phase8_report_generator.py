"""Phase 8 tests for report normalization, assembly, and schema export."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
import pytest

from site_dna.core.config import ScanConfig, Settings
from site_dna.core.context import ScanContext
from site_dna.models.common import CheckStatus, ModuleError, ModuleResult, ModuleStatus
from site_dna.models.page import PageData
from site_dna.models.performance import Performance, StrategyPerformance
from site_dna.models.report import Report, WebsiteContent
from site_dna.models.seo import CheckRecord, SeoAnalysis
from site_dna.models.visual import VisualIdentity
from site_dna.schema.schema_export import DEFAULT_SCHEMA_PATH, build_schema, export_schema
from site_dna.services.normalizer import (
    normalize_issue,
    normalize_list,
    normalize_number,
    normalize_text,
    normalize_url,
)
from site_dna.services.report_generator import build_report, write_report


def _context(tmp_path: Path, *, status: bool = True) -> ScanContext:
    settings = Settings(app_env="test", log_level="WARNING")
    config = ScanConfig(
        input_url="https://example.com",
        permission_attested=status,
        max_pages=5,
        max_depth=1,
    )
    return ScanContext(
        config=config,
        settings=settings,
        scan_id="scan123",
        output_dir=tmp_path / "scan123",
        logger=logging.getLogger("test.phase8"),
        started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def _results(statuses=None):
    statuses = statuses or {}
    pages = [
        PageData(url="https://example.com/", final_url="https://example.com/", title="Home"),
        PageData(url="https://example.com/about", final_url="https://example.com/about", title="About"),
    ]
    content = WebsiteContent(pages=pages, total_pages=2, total_words=25)
    performance = Performance(
        mobile=StrategyPerformance(status=ModuleStatus.ok, score=90),
        desktop=StrategyPerformance(status=ModuleStatus.ok, score=95),
    )
    seo = SeoAnalysis(
        checks=[
            CheckRecord(
                id="title",
                scope="page",
                url="https://example.com/",
                status=CheckStatus.passed,
                confidence="high",
            )
        ]
    )
    return {
        "website_content": ModuleResult[WebsiteContent](
            status=statuses.get("website_content", ModuleStatus.ok),
            duration_ms=120,
            data=content,
            warnings=["content warning"],
        ),
        "visual_identity": ModuleResult[VisualIdentity](
            status=statuses.get("visual_identity", ModuleStatus.ok),
            duration_ms=80,
            data=VisualIdentity(sampled_elements=10),
        ),
        "performance": ModuleResult[Performance](
            status=statuses.get("performance", ModuleStatus.ok),
            duration_ms=300,
            data=performance,
            errors=[ModuleError(code="psi", message="partial field data")],
        ),
        "seo_analysis": ModuleResult[SeoAnalysis](
            status=statuses.get("seo_analysis", ModuleStatus.ok),
            duration_ms=50,
            data=seo,
        ),
    }


def test_normalizers_are_pure_and_null_safe():
    assert normalize_url(" https://Example.com/a/?utm_source=x#frag ") == "https://example.com/a"
    assert normalize_url("") is None
    assert normalize_text("  hello \n world  ") == "hello world"
    assert normalize_text("   ") is None
    assert normalize_number(" 12.0 ") == 12
    assert normalize_number(True) is None
    assert normalize_list([1, None, 2]) == [1, 2]
    assert normalize_list("x") == ["x"]
    assert normalize_issue("title", url=" https://example.com/a#x ", message=" Missing ", confidence="high") == {
        "id": "title",
        "url": "https://example.com/a",
        "message": "Missing",
        "confidence": "high",
    }


def test_build_report_maps_module_results_and_metadata(tmp_path):
    report = build_report(_context(tmp_path), _results())

    assert report.scan_id == "scan123"
    assert report.project_info.input_url == "https://example.com"
    assert report.project_info.final_url == "https://example.com/"
    assert report.project_info.domain == "example.com"
    assert report.project_info.permission_attested is True
    assert report.project_info.scan_status == "completed"
    assert report.website_content.status is ModuleStatus.ok
    assert report.website_content.data.total_pages == 2
    assert report.visual_identity.data.sampled_elements == 10
    assert report.performance.data.mobile.score == 90
    assert report.seo_analysis.data.checks[0].id == "title"
    assert report.execution_summary.module_results == {
        "website_content": "ok",
        "visual_identity": "ok",
        "performance": "ok",
        "seo_analysis": "ok",
    }
    assert report.execution_summary.warnings == ["content warning"]
    assert report.execution_summary.errors[0].code == "psi"
    assert report.execution_summary.timings["website_content"] == 0.12


def test_scan_status_maps_partial_and_failed(tmp_path):
    partial = build_report(
        _context(tmp_path),
        _results({"seo_analysis": ModuleStatus.partial}),
    )
    assert partial.project_info.scan_status == "partial"

    failed = build_report(
        _context(tmp_path),
        {
            "website_content": ModuleResult[WebsiteContent](
                status=ModuleStatus.failed,
                duration_ms=1,
            ),
            "visual_identity": ModuleResult[VisualIdentity](
                status=ModuleStatus.failed,
                duration_ms=1,
            ),
            "performance": ModuleResult[Performance](
                status=ModuleStatus.failed,
                duration_ms=1,
            ),
            "seo_analysis": ModuleResult[SeoAnalysis](
                status=ModuleStatus.failed,
                duration_ms=1,
            ),
        },
    )
    assert failed.project_info.scan_status == "failed"


def test_missing_module_data_uses_null_and_empty_lists(tmp_path):
    results = _results()
    results["website_content"] = ModuleResult[WebsiteContent](
        status=ModuleStatus.partial,
        reason="no_pages",
        duration_ms=5,
    )

    report = build_report(_context(tmp_path), results)

    assert report.website_content.data.pages == []
    assert report.website_content.data.total_pages == 0
    assert report.project_info.final_url is None
    assert report.project_info.domain == "example.com"


def test_write_report_is_atomic_and_schema_valid(tmp_path):
    report = build_report(_context(tmp_path), _results())
    path = write_report(report, tmp_path / "out")

    assert path == tmp_path / "out" / "report.json"
    assert not (tmp_path / "out" / ".report.json.tmp").exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    Report.model_validate(payload)
    jsonschema.validate(payload, build_schema())


def test_schema_export_matches_report_model_and_is_valid(tmp_path):
    path = export_schema(tmp_path / "report.schema.json")
    exported = json.loads(path.read_text(encoding="utf-8"))

    assert exported == build_schema()
    assert exported["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    jsonschema.Draft202012Validator.check_schema(exported)
    assert DEFAULT_SCHEMA_PATH.exists()


def test_placeholder_report_still_validates_against_exported_schema():
    from site_dna.scan import build_placeholder_report

    report = build_placeholder_report(
        scan_id="placeholder",
        input_url="https://example.com",
        config={"max_pages": 1},
    )
    jsonschema.validate(json.loads(report.model_dump_json()), build_schema())


@pytest.mark.parametrize(
    "value,expected",
    [(float("nan"), None), (float("inf"), None), ("not-a-number", None), (0, 0)],
)
def test_normalize_number_rejects_non_finite(value, expected):
    assert normalize_number(value) == expected
