"""Security boundary and defensive isolation tests for Site DNA Phase 09."""

import pytest

from site_dna.analysis.security_privacy.context_builder import (
    SecurityPrivacyContextBuilder,
    sanitize_headers,
)
from site_dna.core.security import SecurityValidationError
from site_dna.schemas.security_privacy import (
    CookieAttributeRecord,
    SecurityPrivacyAnalysisRequest,
)


def test_path_traversal_rejection_in_crawl_id():
    """Verify that path traversal in crawl_run_id is blocked with SecurityValidationError."""
    builder = SecurityPrivacyContextBuilder()

    bad_ids = [
        "../../etc/passwd",
        "../..\\windows\\system32",
        "crawl-01/../../../secret",
        "run;rm -rf /",
        "run`whoami`",
    ]

    for bad_id in bad_ids:
        req = SecurityPrivacyAnalysisRequest(crawl_run_id=bad_id)
        with pytest.raises(SecurityValidationError):
            builder.build_context(req)


def test_sanitize_headers_redacts_credentials():
    """Verify that authorization, cookies, and tokens are scrubbed from headers."""
    raw_headers = {
        "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.super_secret",
        "cookie": "session_id=12345; user=admin; token=abcde999",
        "set-cookie": "secret_auth=998877; Secure; HttpOnly; SameSite=Strict",
        "x-api-key": "secret-api-key-9999",
        "content-type": "text/html; charset=utf-8",
    }

    cleaned = sanitize_headers(raw_headers)

    # Sensitive headers must be masked or redacted
    assert cleaned["authorization"] == "[REDACTED_SECRET]"
    assert cleaned["cookie"] == "[REDACTED_SECRET]"
    assert cleaned["x-api-key"] == "[REDACTED_SECRET]"
    assert "super_secret" not in cleaned["authorization"]
    assert "abcde999" not in cleaned["cookie"]
    assert "998877" not in cleaned["set-cookie"]
    # Retain structural attributes
    assert "[REDACTED]" in cleaned["set-cookie"]
    assert "Secure" in cleaned["set-cookie"]
    assert "HttpOnly" in cleaned["set-cookie"]
    # Non-sensitive header remains
    assert cleaned["content-type"] == "text/html; charset=utf-8"


def test_cookie_record_masks_values():
    """Verify that CookieAttributeRecord does not expose secret values."""
    cookie = CookieAttributeRecord(
        name="sessionid",
        is_secure=True,
        is_http_only=True,
        same_site="Lax",
    )
    dumped = cookie.model_dump()
    # Ensure raw secret attribute is never exposed
    assert "value" not in dumped or dumped.get("value") is None
    assert dumped["name"] == "sessionid"
    assert dumped["is_secure"] is True
    assert dumped["is_http_only"] is True
