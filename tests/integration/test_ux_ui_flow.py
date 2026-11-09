"""Integration tests for UXUIFlow and UXAnalysisService."""

from pathlib import Path

from site_dna.analysis.ux_ui.service import UXAnalysisService
from site_dna.flows.ux_ui_flow import UXUIFlow
from site_dna.schemas.ux_ui import UXAnalysisRequest
from site_dna.tools.ux_ui_tool import UXUITool

FIXTURES_DIR = Path("tests/fixtures/ux_ui")


def test_ux_service_fixture_a_offline(tmp_path):
    """Verify that UXAnalysisService executes completely in offline mode on Fixture A."""
    base_dir = str(FIXTURES_DIR / "fixture_a_good_ux" / "runs")
    service = UXAnalysisService(base_dir=base_dir)

    req = UXAnalysisRequest(
        visual_run_id="vis-a",
        crawl_run_id="crawl-a",
        max_pages=2,
        language="ar",
        save_results=True,
    )
    report = service.analyze_ux(req, offline_mode=True)

    assert report.analysis_status == "completed"
    assert report.overall_score is not None
    assert 0.0 <= report.overall_score <= 100.0
    assert len(report.score_explanations) == 6
    assert report.navigation_assessment is not None
    assert report.interaction_assessment is not None
    assert report.forms_assessment is not None
    assert report.responsive_assessment is not None
    assert report.accessibility_assessment is not None
    assert report.content_assessment is not None
    assert len(report.user_journeys) > 0
    assert report.report_markdown_path is not None
    assert Path(report.report_markdown_path).exists()


def test_ux_ui_flow_execution_fixture_a():
    """Verify end-to-end execution of CrewAI UXUIFlow on Fixture A."""
    base_dir = str(FIXTURES_DIR / "fixture_a_good_ux" / "runs")
    flow = UXUIFlow(
        visual_run_id="vis-a",
        crawl_run_id="crawl-a",
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


def test_ux_ui_tool_execution():
    """Verify CrewAI BaseTool wrapper UXUITool produces valid JSON report string."""
    base_dir = str(FIXTURES_DIR / "fixture_a_good_ux" / "runs")
    tool = UXUITool()

    # We patch base_dir for the service in tool
    from unittest.mock import patch

    with patch("site_dna.tools.ux_ui_tool.UXAnalysisService") as mock_srv_cls:
        srv_instance = UXAnalysisService(base_dir=base_dir)
        mock_srv_cls.return_value = srv_instance

        result_str = tool._run(visual_run_id="vis-a", crawl_run_id="crawl-a", save_results=False)
        assert "schema_version" in result_str
        assert "overall_score" in result_str
