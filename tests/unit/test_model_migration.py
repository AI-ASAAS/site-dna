"""Unit tests verifying Gemini 3.6 Flash migration and model isolation."""

from site_dna.analysis.visual_identity.cache import VisualIdentityCache
from site_dna.analysis.visual_identity.context_builder import VisualAnalysisContext
from site_dna.analysis.visual_identity.image_preprocessor import PreparedImage
from site_dna.core.config import Settings
from site_dna.core.llm import format_crewai_gemini_model
from site_dna.schemas.visual_identity import VisualAnalysisStatistics, VisualIdentityReport


def test_default_model_is_gemini_36_flash():
    """Verify that default settings configure gemini-3.6-flash across all active configurations."""
    settings = Settings(_env_file=None)
    assert settings.gemini_model == "gemini-3.6-flash"
    assert settings.visual_analysis_model == "gemini-3.6-flash"


def test_crewai_model_formatting_for_gemini_36():
    """Verify that format_crewai_gemini_model produces gemini/gemini-3.6-flash."""
    assert format_crewai_gemini_model("gemini-3.6-flash") == "gemini/gemini-3.6-flash"
    assert format_crewai_gemini_model("gemini/gemini-3.6-flash") == "gemini/gemini-3.6-flash"


def test_schemas_default_to_gemini_36():
    """Verify that visual identity report and statistics schemas default to gemini-3.6-flash."""
    stats = VisualAnalysisStatistics()
    assert stats.model_name == "gemini-3.6-flash"

    report = VisualIdentityReport(
        crawl_run_id="crawl-test",
        visual_run_id="vis-test",
        site_url="https://example.com",
        summary_arabic="ملخص اختباري",
        summary_english="Test summary",
    )
    assert report.model_name == "gemini-3.6-flash"


def test_cache_strictly_isolates_gemini_38_from_gemini_36(tmp_path):
    """Verify that cached entries for gemini-3.8-flash never match or collide with gemini-3.6-flash."""
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

    key_38 = VisualIdentityCache.compute_cache_key("gemini-3.8-flash", mock_context, [mock_image])
    key_36 = VisualIdentityCache.compute_cache_key("gemini-3.6-flash", mock_context, [mock_image])

    # Keys must be completely different
    assert key_38 != key_36

    # Test cache storage and retrieval isolation
    cache = VisualIdentityCache(cache_dir=str(tmp_path), enabled=True)
    cache.set(key_38, {"model_name": "gemini-3.8-flash", "visual_summary_arabic": "قديم"})

    # Looking up key_38 expecting gemini-3.6-flash must return None
    assert cache.get(key_38, expected_model="gemini-3.6-flash") is None

    # Looking up key_36 when not cached must return None
    assert cache.get(key_36, expected_model="gemini-3.6-flash") is None
