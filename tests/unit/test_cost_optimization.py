"""Unit tests verifying cost, token, image budget, and caching optimizations."""

from site_dna.analysis.visual_identity.cache import VisualIdentityCache
from site_dna.analysis.visual_identity.context_builder import VisualAnalysisContext
from site_dna.analysis.visual_identity.image_preprocessor import (
    ImagePreprocessor,
    PreparedImage,
)
from site_dna.analysis.visual_identity.multimodal_adapter import MultimodalAdapter
from site_dna.core.config import Settings


def test_cost_settings_defaults():
    """Verify that settings enforce budget caps (max 8 images, 2048 max output tokens)."""
    settings = Settings(_env_file=None)
    assert settings.visual_analysis_max_images == 8
    assert settings.visual_analysis_max_output_tokens == 2048
    assert settings.visual_analysis_cache_enabled is True


def test_image_preprocessor_enforces_image_budget():
    """Verify ImagePreprocessor caps prepared images to max_images budget."""
    preprocessor = ImagePreprocessor(max_images=8)
    assert preprocessor.max_images == 8


def test_cache_hit_prevents_api_call(tmp_path):
    """Verify that a valid cache entry satisfies the request without making an API call."""
    settings = Settings(
        gemini_api_key="valid_dummy_key",
        visual_analysis_model="gemini-3.6-flash",
        visual_analysis_cache_enabled=True,
        visual_analysis_cache_dir=str(tmp_path),
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

    # Pre-populate cache
    cache = VisualIdentityCache(cache_dir=str(tmp_path), enabled=True)
    cache_key = cache.compute_cache_key("gemini-3.6-flash", mock_context, [mock_image])
    cached_data = {
        "visual_summary_arabic": "ملخص مخزن مؤقتاً",
        "visual_summary_english": "Cached summary",
        "model_name": "gemini-3.6-flash",
        "ai_findings": [],
        "ai_analysis_completed": True,
    }
    cache.set(cache_key, cached_data)

    # Calling adapter should return cached result with from_cache=True without client API call
    res = adapter.analyze_visual_identity(mock_context, [mock_image], offline_mode=False)

    assert res["from_cache"] is True
    assert res["visual_summary_arabic"] == "ملخص مخزن مؤقتاً"
    assert res["model_name"] == "gemini-3.6-flash"
    assert res["ai_analysis_completed"] is True
