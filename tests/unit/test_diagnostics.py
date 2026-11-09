"""Unit tests for Gemini diagnostics, bounded retries, and error classifications."""

from unittest.mock import MagicMock, patch

import pytest
from google.genai import errors as genai_errors

from site_dna.core.config import Settings
from site_dna.services.gemini_diagnostics import (
    DiagnosticStatus,
    classify_genai_error,
    sanitize_message,
)
from site_dna.services.gemini_diagnostics import (
    test_direct_gemini_connection as run_direct_gemini_diagnostic,
)


def test_missing_api_key_returns_auth_error():
    """Condition 1: Missing API key fails immediately with 0 attempts."""
    settings = Settings(gemini_api_key=None, app_env="test")
    res = run_direct_gemini_diagnostic(settings=settings)

    assert res.success is False
    assert res.status == DiagnosticStatus.AUTHENTICATION_ERROR
    assert res.attempts == 0
    assert "missing" in res.error_message.lower()


def test_sanitize_message_redacts_api_keys():
    """Ensure that API keys are completely stripped from error strings."""
    raw = (
        "Failed with key AIza_TEST_MOCK_SECRET_KEY_123456789 and AQ.TEST_MOCK_TOKEN_987654321"
    )
    cleaned = sanitize_message(raw)
    assert "AIza_TEST" not in cleaned
    assert "AQ.TEST" not in cleaned
    assert "[REDACTED_SECRET]" in cleaned


@pytest.mark.parametrize(
    ("exc", "expected_status", "expected_code"),
    [
        # Condition 2: Invalid API key (401)
        (genai_errors.ClientError(401, "API_KEY_INVALID: Key is invalid"), DiagnosticStatus.AUTHENTICATION_ERROR, 401),
        # Condition 3: Permission denied (403)
        (genai_errors.ClientError(403, "PERMISSION_DENIED for resource"), DiagnosticStatus.PERMISSION_DENIED, 403),
        # Condition 4: Bad request (400)
        (
            genai_errors.ClientError(400, "INVALID_ARGUMENT: unsupported parameter"),
            DiagnosticStatus.INVALID_REQUEST,
            400,
        ),
        # Condition 5: Model not found (404)
        (
            genai_errors.ClientError(404, "NOT_FOUND: Model models/gemini-old is not found"),
            DiagnosticStatus.MODEL_UNAVAILABLE,
            404,
        ),
        # Condition 6: Rate limited (429)
        (genai_errors.ClientError(429, "RESOURCE_EXHAUSTED: Rate limit exceeded"), DiagnosticStatus.RATE_LIMITED, 429),
        # Condition 7: Quota exceeded (429)
        (
            genai_errors.ClientError(429, "RESOURCE_EXHAUSTED: Daily quota exceeded"),
            DiagnosticStatus.QUOTA_EXCEEDED,
            429,
        ),
        # Condition 8: Internal server error (500)
        (genai_errors.ServerError(500, "Internal error"), DiagnosticStatus.SERVICE_UNAVAILABLE, 500),
        # Condition 9: Service unavailable (503)
        (genai_errors.ServerError(503, "UNAVAILABLE: high demand"), DiagnosticStatus.SERVICE_UNAVAILABLE, 503),
        # Condition 10: Deadline exceeded (504)
        (
            genai_errors.ServerError(504, "DEADLINE_EXCEEDED: operation timed out"),
            DiagnosticStatus.REQUEST_TIMEOUT,
            504,
        ),
        # Condition 11: Network timeout
        (TimeoutError("Read timeout on socket"), DiagnosticStatus.REQUEST_TIMEOUT, 408),
        # Condition 12: Network disconnection
        (ConnectionResetError("Connection refused by host"), DiagnosticStatus.NETWORK_ERROR, None),
    ],
)
def test_error_classification_mappings(exc, expected_status, expected_code):
    """Verify exact classification for all standard Google API failure exceptions."""
    status, code, _ = classify_genai_error(exc)
    assert status == expected_status
    assert code == expected_code


@patch("site_dna.services.gemini_diagnostics.genai.Client")
def test_non_retryable_error_fails_immediately_without_retrying(mock_client_cls):
    """Prove that non-retryable errors (e.g. 401 Auth Error) halt after 1 attempt."""
    mock_instance = MagicMock()
    mock_instance.models.generate_content.side_effect = genai_errors.ClientError(401, "API_KEY_INVALID")
    mock_client_cls.return_value = mock_instance

    settings = Settings(gemini_api_key="dummy_key", app_env="test")
    res = run_direct_gemini_diagnostic(
        settings=settings,
        max_attempts=3,
        initial_backoff=0.01,
    )

    assert res.success is False
    assert res.status == DiagnosticStatus.AUTHENTICATION_ERROR
    # Non-retryable must only execute 1 attempt
    assert res.attempts == 1
    assert mock_instance.models.generate_content.call_count == 1


@patch("site_dna.services.gemini_diagnostics.genai.Client")
def test_retryable_error_retries_and_exhausts_budget(mock_client_cls):
    """Condition 14: Retryable error (503) retries up to max_attempts then fails cleanly."""
    mock_instance = MagicMock()
    mock_instance.models.generate_content.side_effect = genai_errors.ServerError(503, "UNAVAILABLE: high demand")
    mock_client_cls.return_value = mock_instance

    settings = Settings(gemini_api_key="dummy_key", app_env="test")
    res = run_direct_gemini_diagnostic(
        settings=settings,
        max_attempts=3,
        initial_backoff=0.01,
        max_backoff=0.02,
    )

    assert res.success is False
    assert res.status == DiagnosticStatus.SERVICE_UNAVAILABLE
    # Proves all 3 attempts were made
    assert res.attempts == 3
    assert mock_instance.models.generate_content.call_count == 3


@patch("site_dna.services.gemini_diagnostics.genai.Client")
def test_retry_recovers_on_transient_failure(mock_client_cls):
    """Verify that a transient 504 on attempt 1 that recovers on attempt 2 succeeds."""
    mock_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "SITE_DNA_GEMINI_OK"

    # Attempt 1 fails with 504, Attempt 2 succeeds
    mock_instance.models.generate_content.side_effect = [
        genai_errors.ServerError(504, "DEADLINE_EXCEEDED"),
        mock_response,
    ]
    mock_client_cls.return_value = mock_instance

    settings = Settings(gemini_api_key="dummy_key", app_env="test")
    res = run_direct_gemini_diagnostic(
        settings=settings,
        max_attempts=3,
        initial_backoff=0.01,
    )

    assert res.success is True
    assert res.status == DiagnosticStatus.SUCCESS
    assert res.attempts == 2
    assert res.response_text == "SITE_DNA_GEMINI_OK"
    assert mock_instance.models.generate_content.call_count == 2
