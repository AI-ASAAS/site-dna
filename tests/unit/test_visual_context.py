"""Unit tests for VisualIdentityContextBuilder (integrity, checksums, dimensions)."""

from pathlib import Path

import pytest
from PIL import Image

from site_dna.analysis.visual_identity.context_builder import (
    ContextValidationError,
    VisualIdentityContextBuilder,
)

FIXTURES_DIR = Path("tests/fixtures/visual_identity")


def test_context_builder_fixture_a():
    """Verify context builder loads and validates clean Fixture A."""
    base_dir = FIXTURES_DIR / "fixture_a" / "runs"
    builder = VisualIdentityContextBuilder(base_dir=str(base_dir))

    context = builder.build_context(visual_run_id="vis-a", crawl_run_id="crawl-a")
    assert context.visual_run_id == "vis-a"
    assert context.crawl_run_id == "crawl-a"
    assert len(context.pages) == 2
    assert len(context.screenshot_files) == 4
    assert len(context.evidence_index) == 2
    assert context.declared_language == "en"
    assert len(context.warnings) == 0


def test_context_builder_checksum_mismatch(tmp_path):
    """Verify that corrupt screenshot checksum raises ContextValidationError."""
    runs_dir = tmp_path / "runs"
    vis_dir = runs_dir / "crawl-corrupt" / "visual" / "vis-corrupt"
    vis_dir.mkdir(parents=True)

    img_file = vis_dir / "shot.png"
    Image.new("RGB", (100, 100), (0, 0, 0)).save(img_file, format="PNG")

    crawl_json = {
        "schema_version": "1.0",
        "run_id": "crawl-corrupt",
        "status": "completed",
        "website_info": {"initial_url": "https://test.com", "canonical_origin": "https://test.com"},
        "pages": [
            {
                "url": "https://test.com/",
                "final_url": "https://test.com/",
                "depth": 0,
                "status_code": 200,
                "metadata": {},
            }
        ],
    }
    (runs_dir / "crawl-corrupt" / "crawl.json").write_text(__import__("json").dumps(crawl_json), encoding="utf-8")

    visual_json = {
        "schema_version": "1.0",
        "crawl_run_id": "crawl-corrupt",
        "visual_run_id": "vis-corrupt",
        "status": "completed",
        "target_origin": "https://test.com",
        "pages": [
            {
                "page_url": "https://test.com/",
                "safe_page_id": "p0",
                "status": "completed",
                "desktop_screenshots": [
                    {
                        "viewport_profile": "desktop",
                        "screenshot_type": "viewport",
                        "file_path": str(img_file.resolve()),
                        "relative_path": "pages/shot.png",
                        "file_size_bytes": 100,
                        "width_px": 100,
                        "height_px": 100,
                        "sha256": "bad_hash_1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
                        "success": True,
                    }
                ],
                "mobile_screenshots": [],
                "colors": [],
                "typography": [],
                "evidence_records": [],
            }
        ],
    }
    (vis_dir / "visual.json").write_text(__import__("json").dumps(visual_json), encoding="utf-8")

    builder = VisualIdentityContextBuilder(base_dir=str(runs_dir))
    with pytest.raises(ContextValidationError, match="Corrupted screenshot checksum"):
        builder.build_context(visual_run_id="vis-corrupt", crawl_run_id="crawl-corrupt")


def test_context_builder_run_id_mismatch(tmp_path):
    """Verify that mismatch between visual artifact crawl_run_id and directory crawl_run_id raises error."""
    runs_dir = tmp_path / "runs"
    vis_dir = runs_dir / "crawl-mismatch" / "visual" / "vis-mismatch"
    vis_dir.mkdir(parents=True)

    crawl_json = {
        "schema_version": "1.0",
        "run_id": "crawl-mismatch",
        "status": "completed",
        "website_info": {"initial_url": "https://test.com", "canonical_origin": "https://test.com"},
        "pages": [],
    }
    (runs_dir / "crawl-mismatch" / "crawl.json").write_text(__import__("json").dumps(crawl_json), encoding="utf-8")

    visual_json = {
        "schema_version": "1.0",
        "crawl_run_id": "different-crawl-id",
        "visual_run_id": "vis-mismatch",
        "status": "completed",
        "target_origin": "https://test.com",
        "pages": [],
    }
    (vis_dir / "visual.json").write_text(__import__("json").dumps(visual_json), encoding="utf-8")

    builder = VisualIdentityContextBuilder(base_dir=str(runs_dir))
    with pytest.raises(ContextValidationError, match="Crawl run ID mismatch"):
        builder.build_context(visual_run_id="vis-mismatch", crawl_run_id="crawl-mismatch")


def test_context_builder_fixture_e_missing_files():
    """Verify that missing screenshot files in Fixture E generate warnings rather than unhandled crashes."""
    base_dir = FIXTURES_DIR / "fixture_e" / "runs"
    builder = VisualIdentityContextBuilder(base_dir=str(base_dir))

    context = builder.build_context(visual_run_id="vis-e", crawl_run_id="crawl-e")
    assert context.visual_run_id == "vis-e"
    assert len(context.warnings) > 0
    assert any("Missing screenshot file" in w for w in context.warnings)
