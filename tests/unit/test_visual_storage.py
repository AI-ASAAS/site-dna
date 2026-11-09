"""Unit tests for VisualStorageManager and safe page id generator."""

import json
from pathlib import Path

from site_dna.schemas.visual import VisualCaptureResult, VisualCaptureStatistics, VisualPageResult
from site_dna.visual.storage import VisualStorageManager, generate_safe_page_id


def test_generate_safe_page_id():
    id1 = generate_safe_page_id("https://example.com/about", index=1)
    assert id1.startswith("page_01_")
    assert "about" in id1
    assert "/" not in id1
    assert "\\" not in id1
    assert ":" not in id1

    # Same URL should produce stable hash suffix
    id2 = generate_safe_page_id("https://example.com/about", index=1)
    assert id1 == id2


def test_visual_storage_manager_hierarchy(tmp_path: Path):
    manager = VisualStorageManager(
        crawl_run_id="crawl-test-123",
        visual_run_id="vis-test-456",
        base_dir=str(tmp_path),
    )

    expected_root = tmp_path / "crawl-test-123" / "visual" / "vis-test-456"
    assert manager.root_visual_dir == expected_root
    assert (expected_root / "pages").exists()

    # Get page dir with traversal attempt
    page_dir = manager.get_page_dir("../../malicious_page")
    # Path traversal should be sanitized out
    assert ".." not in page_dir.name
    assert page_dir.is_relative_to(manager.pages_dir)
    assert page_dir.exists()


def test_visual_storage_manager_save_result_and_manifest(tmp_path: Path):
    manager = VisualStorageManager(
        crawl_run_id="crawl-test-123",
        visual_run_id="vis-test-456",
        base_dir=str(tmp_path),
    )

    result = VisualCaptureResult(
        crawl_run_id="crawl-test-123",
        visual_run_id="vis-test-456",
        status="completed",
        target_origin="https://example.com",
        pages=[
            VisualPageResult(
                page_url="https://example.com",
                safe_page_id="page_00_home",
                status="completed",
            )
        ],
        statistics=VisualCaptureStatistics(
            total_pages_attempted=1,
            desktop_captures_completed=1,
            mobile_captures_completed=1,
            screenshots_saved=2,
        ),
    )

    visual_path = manager.save_visual_result(result)
    assert visual_path.exists()
    assert visual_path.name == "visual.json"

    saved_data = json.loads(visual_path.read_text(encoding="utf-8"))
    assert saved_data["crawl_run_id"] == "crawl-test-123"

    manifest_path = manager.save_manifest(result)
    assert manifest_path.exists()
    assert manifest_path.name == "manifest.json"

    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest_data["schema_version"] == "1.0"
    assert len(manifest_data["pages"]) == 1
    assert manifest_data["pages"][0]["safe_page_id"] == "page_00_home"
