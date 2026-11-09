"""Unit tests for SecurityPrivacyContextBuilder (Phase 09)."""

import json
from pathlib import Path

import pytest

from site_dna.analysis.security_privacy.context_builder import SecurityPrivacyContextBuilder, sanitize_headers
from site_dna.core.security import SecurityValidationError
from site_dna.schemas.security_privacy import SecurityPrivacyAnalysisRequest


def test_sanitize_headers_redaction():
    """Verify sensitive headers like Authorization and Set-Cookie values are strictly redacted."""
    raw = {
        "Content-Type": "application/json",
        "Authorization": "Bearer secret_bearer_token_xyz",
        "Set-Cookie": "session_id=ultra_secret_cookie_token_123; Secure; HttpOnly; SameSite=Lax",
        "X-Api-Key": "secret_key_456",
    }
    cleaned = sanitize_headers(raw)
    assert cleaned["content-type"] == "application/json"
    assert cleaned["authorization"] == "[REDACTED_SECRET]"
    assert cleaned["x-api-key"] == "[REDACTED_SECRET]"
    assert "ultra_secret_cookie_token_123" not in cleaned["set-cookie"]
    assert "[REDACTED]" in cleaned["set-cookie"]
    assert "Secure" in cleaned["set-cookie"]


def test_context_builder_path_traversal_rejection(tmp_path: Path):
    """Verify path traversal attempts in crawl_run_id are rejected."""
    builder = SecurityPrivacyContextBuilder(base_dir=tmp_path / "runs")

    req = SecurityPrivacyAnalysisRequest(crawl_run_id="../../etc/passwd")
    with pytest.raises(SecurityValidationError):
        builder.build_context(req)


def test_context_builder_valid_run(tmp_path: Path):
    """Verify building context from valid crawl run directory."""
    runs_dir = tmp_path / "runs"
    run_dir = runs_dir / "crawl-valid-01"
    run_dir.mkdir(parents=True)

    crawl_payload = {
        "target_url": "https://example.com/",
        "website_info": {"canonical_origin": "https://example.com"},
        "pages": [
            {
                "url": "https://example.com/",
                "status_code": 200,
                "headers": {"content-type": "text/html"},
                "cookies": [{"name": "uid", "value": "secret_123", "secure": True}],
                "raw_html": "<html><body><a href='/privacy'>Privacy</a></body></html>",
            }
        ],
    }
    (run_dir / "crawl.json").write_text(json.dumps(crawl_payload), encoding="utf-8")

    builder = SecurityPrivacyContextBuilder(base_dir=runs_dir)

    req = SecurityPrivacyAnalysisRequest(crawl_run_id="crawl-valid-01")
    ctx = builder.build_context(req)

    assert ctx.security_run_id.startswith("sec-")
    assert ctx.site_origin == "https://example.com"
    assert len(ctx.page_records) == 1
    # Check that cookie secret value was redacted in page record
    assert ctx.page_records[0].cookies[0]["value"] == "[REDACTED]"
