"""Unit tests for quota exhaustion classification, immediate halt, and status handling."""

from unittest.mock import MagicMock, patch

from google.genai import errors as genai_errors

from site_dna.analysis.visual_identity.context_builder import VisualAnalysisContext
from site_dna.analysis.visual_identity.image_preprocessor import PreparedImage
from site_dna.analysis.visual_identity.multimodal_adapter import (
    MultimodalAdapter,
    is_daily_quota_exhausted,
)
from site_dna.analysis.visual_identity.service import VisualIdentityAnalysisService
from site_dna.cli import run_analyze_visual
from site_dna.core.config import Settings
from site_dna.schemas.visual_identity import VisualIdentityAnalysisRequest
from site_dna.services.gemini_diagnostics import (
    DiagnosticStatus,
    classify_genai_error,
)


def test_classify_genai_error_daily_quota():
    """Verify that 429 with Free Tier daily quota exhaustion is classified as DAILY_QUOTA_EXHAUSTED."""
    err_msg = (
        "You exceeded your current quota. Quota exceeded for metric: "
        "generativelanguage.googleapis.com/generate_content_free_tier_requests, "
        "limit: 20, model: gemini-3.6-flash, description: Generate content requests per day limit exceeded on Free Tier. "
        "Please retry in 20h45m."
    )
    exc = genai_errors.ClientError(429, err_msg)

    status, code, msg = classify_genai_error(exc)
    assert status == DiagnosticStatus.DAILY_QUOTA_EXHAUSTED
    assert code == 429
    assert "Daily quota exhausted" in msg


def test_classify_genai_error_transient_rate_limit():
    """Verify that transient 429 RPM limit is classified as RATE_LIMITED."""
    exc = genai_errors.ClientError(429, "Resource has been exhausted (e.g. check quota).")

    status, code, msg = classify_genai_error(exc)
    assert status in (DiagnosticStatus.RATE_LIMITED, DiagnosticStatus.QUOTA_EXCEEDED)
    assert code == 429


def test_is_daily_quota_exhausted_detection():
    """Verify is_daily_quota_exhausted detects daily quota markers and parses retry delay."""
    exc = Exception(
        "Quota exceeded: GenerateRequestsPerDayPerProjectPerModel-FreeTier limit: 20. Please retry in 18h30m."
    )
    is_exhausted, delay = is_daily_quota_exhausted(exc)
    assert is_exhausted is True
    assert delay == "18h30m"

    normal_exc = Exception("Connection reset by peer")
    is_exhausted, delay = is_daily_quota_exhausted(normal_exc)
    assert is_exhausted is False
    assert delay is None


@patch("google.genai.Client")
def test_multimodal_adapter_halts_immediately_on_daily_quota(mock_client_cls):
    """Verify MultimodalAdapter halts retries immediately (0 retries) on daily quota exhaustion."""
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    daily_err = genai_errors.ClientError(
        429,
        "GenerateRequestsPerDayPerProjectPerModel-FreeTier limit exceeded. Retry in 22h.",
    )
    mock_client.models.generate_content.side_effect = daily_err

    settings = Settings(
        gemini_api_key="test_key_12345",
        visual_analysis_model="gemini-3.6-flash",
        visual_analysis_max_retries=3,
        visual_analysis_cache_enabled=False,
    )
    adapter = MultimodalAdapter(settings=settings)

    mock_context = VisualAnalysisContext(
        target_origin="https://example.com",
        crawl_run_id="crawl-1",
        visual_run_id="vis-1",
        pages=[],
        business_context={},
    )
    mock_image = PreparedImage(
        file_path="dummy.png",
        page_url="https://example.com",
        viewport_profile="desktop",
        screenshot_type="viewport",
        width_px=1440,
        height_px=900,
        sha256="abc123def456",
        image_bytes=b"dummybytes",
    )

    res = adapter.analyze_visual_identity(mock_context, [mock_image], offline_mode=False)

    # Must call exactly once (0 retries)
    assert mock_client.models.generate_content.call_count == 1
    assert res["ai_analysis_completed"] is False
    assert res["quota_exhausted"] is True
    assert "deterministic fallback" in res["model_name"]


def test_service_sets_ai_blocked_status_when_quota_exhausted():
    """Verify VisualIdentityAnalysisService assigns 'ai_blocked' status when AI fails."""
    service = VisualIdentityAnalysisService(base_dir="tests/fixtures/visual_identity/fixture_a/runs")

    # Mock adapter returning quota exhausted fallback
    service.multimodal_adapter.analyze_visual_identity = MagicMock(
        return_value={
            "visual_summary_arabic": "ملخص تجريبي حتمي",
            "visual_summary_english": "Deterministic test summary",
            "ai_findings": [],
            "ai_analysis_completed": False,
            "quota_exhausted": True,
            "fallback_reason": "Daily quota limit reached",
            "model_name": "gemini-3.6-flash (deterministic fallback)",
        }
    )

    req = VisualIdentityAnalysisRequest(
        visual_run_id="vis-a",
        crawl_run_id="crawl-a",
        save_results=False,
    )

    report = service.analyze_visual_identity(req, offline_mode=False)

    assert report.analysis_status == "ai_blocked"
    assert report.ai_analysis_completed is False
    assert report.deterministic_analysis_completed is True
    assert report.statistics.quota_exhausted is True
    assert "تعذر استكمال التحليل البصري بالذكاء الاصطناعي" in report.limitations_arabic[0]


@patch("site_dna.analysis.visual_identity.service.VisualIdentityAnalysisService")
def test_cli_exit_code_3_on_ai_blocked(mock_service_cls):
    """Verify CLI exits with code 3 when report status is 'ai_blocked'."""
    mock_service = MagicMock()
    mock_service_cls.return_value = mock_service

    mock_report = MagicMock()
    mock_report.analysis_status = "ai_blocked"
    mock_report.analysis_run_id = "vi-test-123"
    mock_report.site_url = "https://example.com"
    mock_report.overall_score = 75.0
    mock_report.score_explanations = []
    mock_report.findings = []
    mock_report.recommendations = []
    mock_report.statistics.pages_analyzed = 1
    mock_report.statistics.screenshots_processed = 2
    mock_report.statistics.validated_findings = 3
    mock_report.statistics.duration_ms = 120.0
    mock_report.ai_analysis_completed = False
    mock_report.report_markdown_path = None
    mock_service.analyze_visual_identity.return_value = mock_report

    exit_code = run_analyze_visual(visual_run_id="vis-test-123", offline=False)
    assert exit_code == 3


def test_cli_exit_code_2_on_missing_input():
    """Verify CLI exits with code 2 when neither run_id nor manifest_file is provided."""
    exit_code = run_analyze_visual(visual_run_id=None, manifest_file=None)
    assert exit_code == 2
