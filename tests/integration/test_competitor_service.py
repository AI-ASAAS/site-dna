"""Integration tests for CompetitorIntelligenceService (Phase 08)."""

from pathlib import Path

from site_dna.analysis.competitor_intelligence.service import CompetitorIntelligenceService
from site_dna.core.config import Settings
from site_dna.schemas.competitor_intelligence import CompetitorAnalysisRequest
from tests.fixtures.competitor_intelligence.test_fixtures import (
    COMPETITOR_1_CRAWL_DATA,
    PRIMARY_CRAWL_DATA,
)


def test_competitor_service_analyze_mock_end_to_end(tmp_path: Path):
    settings = Settings(
        app_name="Site DNA Test",
        app_env="test",
        gemini_model="gemini-3.6-flash",
    )

    # Monkeypatch the base_dir to tmp_path
    service = CompetitorIntelligenceService(settings=settings)
    service.base_dir = tmp_path

    # Pre-populate primary and competitor runs on disk
    primary_dir = tmp_path / "run-primary"
    primary_dir.mkdir(parents=True, exist_ok=True)
    (primary_dir / "crawl.json").write_text(__import__("json").dumps(PRIMARY_CRAWL_DATA), encoding="utf-8")

    comp_dir = tmp_path / "run-competitor"
    comp_dir.mkdir(parents=True, exist_ok=True)
    (comp_dir / "crawl.json").write_text(__import__("json").dumps(COMPETITOR_1_CRAWL_DATA), encoding="utf-8")

    req = CompetitorAnalysisRequest(
        primary_url="https://primary-crm.example.com",
        primary_run_id="run-primary",
        competitor_urls=["https://rival-crm.example.com"],
        competitor_run_ids=["run-competitor"],
        offline_mode=True,
    )

    report = service.analyze(req)

    assert report.primary_site.canonical_origin == "https://primary-crm.example.com"
    assert len(report.competitor_sites) == 1
    assert report.scores.overall_score is not None and report.scores.overall_score >= 0.0
    assert len(report.feature_matrix) > 0
    assert len(report.findings) > 0
    assert len(report.recommendations) > 0

    # Verify artifacts on disk
    art_dir = tmp_path / "run-primary" / "analysis" / "competitors" / report.comparison_run_id
    assert art_dir.exists()
    assert (art_dir / "report.md").exists()
    assert (art_dir / "analysis.json").exists()
    assert (art_dir / "matrix.json").exists()
    assert (art_dir / "findings.json").exists()
    assert (art_dir / "recommendations.json").exists()

    # Check report content contains Arabic markdown headers
    md_content = (art_dir / "report.md").read_text(encoding="utf-8")
    assert "# تقرير استخبارات المنافسين والمقارنة المعيارية الرقمية" in md_content
    assert "gemini-3.6-flash" in md_content.lower()
