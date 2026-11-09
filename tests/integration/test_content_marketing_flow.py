"""Integration tests for ContentMarketingFlow, Tool, and Service."""

from pathlib import Path
from unittest.mock import patch

from site_dna.analysis.content_marketing.service import ContentMarketingAnalysisService
from site_dna.flows.content_marketing_flow import ContentMarketingFlow
from site_dna.schemas.content_marketing import ContentAnalysisRequest
from site_dna.tools.content_marketing_tool import ContentMarketingTool

FIXTURES_DIR = Path("tests/fixtures/content_marketing")


def test_content_service_fixture_a_offline():
    """Verify that ContentMarketingAnalysisService executes completely in offline mode on Fixture A."""
    base_dir = str(FIXTURES_DIR / "fixture_a_clear_messaging" / "runs")
    service = ContentMarketingAnalysisService(base_dir=base_dir)

    req = ContentAnalysisRequest(
        crawl_run_id="crawl-a",
        max_pages=3,
        language="ar",
        save_results=True,
    )
    report = service.analyze_content(req, offline_mode=True)

    assert report.analysis_status == "completed"
    assert report.overall_score is not None
    assert 70.0 <= report.overall_score <= 100.0
    assert len(report.scores) == 7
    assert report.content_inventory.total_pages == 3
    assert report.value_proposition is not None
    assert report.messaging is not None
    assert report.services_and_products is not None
    assert report.ctas is not None
    assert len(report.recommendations) > 0
    assert len(report.rewrite_proposals) > 0
    assert report.report_markdown_path is not None
    assert Path(report.report_markdown_path).exists()


def test_content_marketing_flow_execution_fixture_a():
    """Verify end-to-end execution of CrewAI ContentMarketingFlow on Fixture A."""
    base_dir = str(FIXTURES_DIR / "fixture_a_clear_messaging" / "runs")
    flow = ContentMarketingFlow(
        crawl_run_id="crawl-a",
        max_pages=3,
        language="ar",
        offline_mode=True,
        base_dir=base_dir,
    )

    final_state = flow.kickoff()

    assert final_state.execution_status == "completed"
    assert final_state.report is not None
    assert final_state.report.overall_score is not None
    assert final_state.report.analysis_status == "completed"


def test_content_marketing_tool_execution():
    """Verify CrewAI BaseTool wrapper ContentMarketingTool produces valid JSON report string."""
    base_dir = str(FIXTURES_DIR / "fixture_a_clear_messaging" / "runs")
    tool = ContentMarketingTool()

    with patch("site_dna.tools.content_marketing_tool.ContentMarketingAnalysisService") as mock_srv_cls:
        srv_instance = ContentMarketingAnalysisService(base_dir=base_dir)
        mock_srv_cls.return_value = srv_instance

        result_str = tool._run(crawl_run_id="crawl-a", save_results=False)
        assert "schema_version" in result_str
        assert "overall_score" in result_str
