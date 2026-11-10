"""Phase 1 CLI permission and placeholder report tests."""

import json
import sys

import pytest

from site_dna.cli import main, run_scan_cli
from site_dna.models.common import ModuleStatus
from site_dna.models.report import Report


def _report_paths(output_dir):
    return list(output_dir.glob("*/report.json"))


def test_scan_without_permission_flag_exits_2_and_writes_nothing(tmp_path, capsys) -> None:
    exit_code = run_scan_cli(
        url="https://example.com",
        i_have_permission=False,
        output_dir=str(tmp_path),
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "--i-have-permission" in captured.err
    assert list(tmp_path.iterdir()) == []


def test_scan_writes_schema_valid_placeholder_report(tmp_path) -> None:
    exit_code = run_scan_cli(
        url="https://example.com",
        i_have_permission=True,
        output_dir=str(tmp_path),
    )

    assert exit_code == 0
    reports = _report_paths(tmp_path)
    assert len(reports) == 1

    payload = json.loads(reports[0].read_text(encoding="utf-8"))
    report = Report.model_validate(payload)

    assert report.project_info.input_url == "https://example.com"
    assert report.project_info.permission_attested is True
    assert report.project_info.tool_version
    assert report.website_content.status is ModuleStatus.skipped
    assert report.visual_identity.status is ModuleStatus.skipped
    assert report.performance.status is ModuleStatus.skipped
    assert report.seo_analysis.status is ModuleStatus.skipped
    assert (reports[0].parent / "scan.log").exists()


def test_scan_config_overrides_are_recorded(tmp_path) -> None:
    exit_code = run_scan_cli(
        url="https://example.com",
        i_have_permission=True,
        max_pages=5,
        max_depth=1,
        embed_images=True,
        output_dir=str(tmp_path),
    )

    assert exit_code == 0
    reports = _report_paths(tmp_path)
    report = Report.model_validate_json(reports[0].read_text(encoding="utf-8"))

    assert report.project_info.config["max_pages"] == 5
    assert report.project_info.config["max_depth"] == 1
    assert report.project_info.config["embed_images"] is True


def test_main_scan_missing_permission_exits_2(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["site-dna", "scan", "https://example.com", "--output-dir", str(tmp_path)],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 2
    assert list(tmp_path.iterdir()) == []


def test_main_scan_with_permission_writes_report(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "site-dna",
            "scan",
            "https://example.com",
            "--i-have-permission",
            "--output-dir",
            str(tmp_path),
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0
    assert len(_report_paths(tmp_path)) == 1
