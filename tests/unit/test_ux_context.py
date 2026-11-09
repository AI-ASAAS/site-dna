"""Unit tests for UXContextBuilder (integrity, checksums, dimensions, traversal)."""

from pathlib import Path

import pytest

from site_dna.analysis.ux_ui.context_builder import (
    UXContextBuilder,
    UXContextValidationError,
)

FIXTURES_DIR = Path("tests/fixtures/ux_ui")


def test_ux_context_builder_fixture_a():
    """Verify UX context builder loads and validates clean Fixture A."""
    base_dir = FIXTURES_DIR / "fixture_a_good_ux" / "runs"
    builder = UXContextBuilder(base_dir=str(base_dir))

    context = builder.build_context(visual_run_id="vis-a", crawl_run_id="crawl-a")
    assert context.visual_run_id == "vis-a"
    assert context.crawl_run_id == "crawl-a"
    assert len(context.pages) == 2
    assert len(context.screenshot_files) == 4
    assert len(context.evidence_index) == 2
    assert context.declared_language == "ar"
    assert len(context.warnings) == 0


def test_ux_context_builder_path_traversal():
    """Verify that path traversal in identifiers is rejected."""
    builder = UXContextBuilder(base_dir="runs")

    with pytest.raises(UXContextValidationError, match="Path traversal"):
        builder.build_context(visual_run_id="../../etc/passwd")

    with pytest.raises(UXContextValidationError, match="Path traversal"):
        builder.build_context(visual_run_id="vis-valid", crawl_run_id="../secret")


def test_ux_context_builder_missing_run():
    """Verify that non-existent visual run raises FileNotFoundError."""
    builder = UXContextBuilder(base_dir="tests/fixtures/ux_ui/fixture_a_good_ux/runs")

    with pytest.raises(FileNotFoundError):
        builder.build_context(visual_run_id="vis-nonexistent")


def test_ux_context_builder_checksum_mismatch():
    """Verify that Fixture G with corrupted/missing screenshot fails verification."""
    base_dir = FIXTURES_DIR / "fixture_g_incomplete_evidence" / "runs"
    builder = UXContextBuilder(base_dir=str(base_dir))

    with pytest.raises(UXContextValidationError):
        builder.build_context(visual_run_id="vis-g", crawl_run_id="crawl-g")
