"""Integration tests for SecurityPrivacyFlow and service execution."""

import json
from pathlib import Path

import pytest

from site_dna.flows.security_privacy_flow import SecurityPrivacyFlow


@pytest.mark.asyncio
async def test_security_privacy_flow_execution(tmp_path: Path, monkeypatch):
    """Verify that SecurityPrivacyFlow runs end-to-end and captures completed state."""
    runs_dir = tmp_path / "runs"
    crawl_dir = runs_dir / "crawl-flow-test-01"
    crawl_dir.mkdir(parents=True)

    crawl_payload = {
        "target_url": "https://secure-flow.example.com/",
        "website_info": {"canonical_origin": "https://secure-flow.example.com"},
        "pages": [
            {
                "url": "https://secure-flow.example.com/",
                "status_code": 200,
                "headers": {
                    "strict-transport-security": "max-age=31536000; includeSubDomains",
                    "content-security-policy": "default-src 'self'",
                    "x-content-type-options": "nosniff",
                },
                "cookies": [],
                "raw_html": "<html><body><a href='/privacy'>Privacy Policy</a></body></html>",
            }
        ],
    }
    (crawl_dir / "crawl.json").write_text(json.dumps(crawl_payload), encoding="utf-8")

    # Patch runs directory to tmp_path
    monkeypatch.chdir(tmp_path)

    flow = SecurityPrivacyFlow(
        crawl_run_id="crawl-flow-test-01",
        deterministic_only=True,
        offline_mode=True,
    )

    result_state = flow.kickoff()

    assert result_state.execution_status == "completed"
    assert result_state.report is not None
    assert result_state.report.crawl_run_id == "crawl-flow-test-01"
    assert result_state.report.scores.overall_score > 0
    assert (crawl_dir / "analysis" / "security-privacy").exists()
