"""Integration tests for VisualIdentityFlow and VisualIdentityAnalysisService."""

from pathlib import Path

from site_dna.analysis.visual_identity.service import VisualIdentityAnalysisService
from site_dna.flows.visual_identity_flow import VisualIdentityFlow
from site_dna.schemas.visual_identity import VisualIdentityAnalysisRequest

FIXTURES_DIR = Path("tests/fixtures/visual_identity")


def test_service_fixture_a_offline():
    """Verify end-to-end service execution on Fixture A produces high visual identity score."""
    base_dir = str(FIXTURES_DIR / "fixture_a" / "runs")
    service = VisualIdentityAnalysisService(base_dir=base_dir)

    req = VisualIdentityAnalysisRequest(
        visual_run_id="vis-a",
        crawl_run_id="crawl-a",
        save_results=False,
    )
    report = service.analyze_visual_identity(req, offline_mode=True)

    assert report.analysis_status == "completed"
    assert report.site_url == "https://site-a.com"
    assert report.overall_score is not None
    assert report.overall_score >= 80.0
    assert len(report.score_explanations) == 5
    assert report.statistics.pages_analyzed == 2
    assert report.statistics.screenshots_processed == 4


def test_service_fixture_b_inconsistent():
    """Verify service execution on Fixture B detects multiple issues and lowers score."""
    base_dir = str(FIXTURES_DIR / "fixture_b" / "runs")
    service = VisualIdentityAnalysisService(base_dir=base_dir)

    req = VisualIdentityAnalysisRequest(
        visual_run_id="vis-b",
        crawl_run_id="crawl-b",
        save_results=False,
    )
    report = service.analyze_visual_identity(req, offline_mode=True)

    assert report.analysis_status == "completed"
    assert report.overall_score is not None
    assert report.overall_score < 92.0
    assert len(report.findings) >= 5
    assert len(report.recommendations) >= 5


def test_visual_identity_flow_execution():
    """Verify CrewAI VisualIdentityFlow runs end-to-end and updates flow state."""
    base_dir = str(FIXTURES_DIR / "fixture_a" / "runs")
    flow = VisualIdentityFlow(
        visual_run_id="vis-a",
        crawl_run_id="crawl-a",
        offline_mode=True,
        base_dir=base_dir,
    )

    state = flow.kickoff()

    assert state.execution_status == "completed"
    assert state.report is not None
    assert state.report.overall_score >= 80.0
    assert state.report.site_url == "https://site-a.com"
