"""Integration tests for TechnicalSEOFlow, TechnicalSEOTool, and TechnicalSEOAnalysisService."""

from pathlib import Path
from unittest.mock import patch

from site_dna.analysis.technical_seo.service import TechnicalSEOAnalysisService
from site_dna.flows.technical_seo_flow import TechnicalSEOFlow
from site_dna.schemas.technical_seo import TechnicalSEOAnalysisRequest
from site_dna.tools.technical_seo_tool import TechnicalSEOTool

FIXTURES_DIR = Path("tests/fixtures/technical_seo")


def test_technical_seo_service_fixture_a_offline():
    """Verify that TechnicalSEOAnalysisService executes completely in offline mode on Fixture A."""
    base_dir = str(FIXTURES_DIR / "fixture_a_healthy" / "runs")
    service = TechnicalSEOAnalysisService(base_dir=base_dir)

    req = TechnicalSEOAnalysisRequest(
        crawl_run_id="crawl-a",
        visual_run_id="vis-a",
        max_pages=2,
        language="ar",
        save_results=True,
    )
    report = service.analyze_technical_seo(req, offline_mode=True)

    assert report.analysis_status == "completed"
    assert report.overall_score is not None
    assert 80.0 <= report.overall_score <= 100.0
    assert len(report.scores) == 6
    assert report.crawlability.status == "permitted"
    assert report.indexability.status == "potentially_indexable"
    assert report.robots.is_present is True
    assert report.sitemap.sitemap_found is True
    assert report.canonical.self_referencing_count == 2
    assert report.redirects.redirect_count == 0
    assert report.metadata.missing_title_count == 0
    assert report.structured_data.total_schemas_found >= 1
    assert report.javascript_seo.status == "consistent"
    assert report.mobile_seo.viewport_configured is True
    assert report.core_web_vitals is not None
    assert report.core_web_vitals.inp_source == "not_measured"
    assert report.core_web_vitals.inp_ms is None
    assert report.report_markdown_path is not None
    assert Path(report.report_markdown_path).exists()


def test_technical_seo_flow_execution_fixture_a():
    """Verify end-to-end execution of CrewAI TechnicalSEOFlow on Fixture A."""
    base_dir = str(FIXTURES_DIR / "fixture_a_healthy" / "runs")
    flow = TechnicalSEOFlow(
        crawl_run_id="crawl-a",
        visual_run_id="vis-a",
        max_pages=2,
        language="ar",
        offline_mode=True,
        base_dir=base_dir,
    )

    final_state = flow.kickoff()

    assert final_state.execution_status == "completed"
    assert final_state.report is not None
    assert final_state.report.overall_score is not None
    assert final_state.report.analysis_status == "completed"


def test_technical_seo_tool_execution():
    """Verify CrewAI BaseTool wrapper TechnicalSEOTool produces valid JSON report string."""
    base_dir = str(FIXTURES_DIR / "fixture_a_healthy" / "runs")
    tool = TechnicalSEOTool()

    with patch("site_dna.tools.technical_seo_tool.TechnicalSEOAnalysisService") as mock_srv_cls:
        srv_instance = TechnicalSEOAnalysisService(base_dir=base_dir)
        mock_srv_cls.return_value = srv_instance

        result_str = tool._run(crawl_run_id="crawl-a", visual_run_id="vis-a", save_results=False)
        assert "Overall Score" in result_str
        assert "Run ID" in result_str
