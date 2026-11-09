"""Direct Google Gemini diagnostic service with bounded retries and error classification."""

import random
import re
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types
from pydantic import BaseModel, Field

from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger

logger = get_logger(__name__)

DIAGNOSTIC_PROMPT = "Return exactly: SITE_DNA_GEMINI_OK"
EXPECTED_RESPONSE_SUBSTRING = "SITE_DNA_GEMINI_OK"

# Regex for stripping sensitive key tokens from error strings
SECRET_REDACTION_PATTERN = re.compile(
    r"(AIza[0-9A-Za-z_-]{20,}|AQ\.[0-9A-Za-z_-]{15,}|key=[^&\s'\"]+)",
    re.IGNORECASE,
)


class DiagnosticStatus(str, Enum):
    """Normalized diagnostic outcome classifications."""

    SUCCESS = "SUCCESS"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    INVALID_REQUEST = "INVALID_REQUEST"
    RATE_LIMITED = "RATE_LIMITED"
    RATE_LIMITED_TRANSIENT = "RATE_LIMITED_TRANSIENT"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    DAILY_QUOTA_EXHAUSTED = "DAILY_QUOTA_EXHAUSTED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    REQUEST_TIMEOUT = "REQUEST_TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


# Non-retryable statuses fail immediately without burning retry budget
NON_RETRYABLE_STATUSES = {
    DiagnosticStatus.AUTHENTICATION_ERROR,
    DiagnosticStatus.PERMISSION_DENIED,
    DiagnosticStatus.MODEL_UNAVAILABLE,
    DiagnosticStatus.INVALID_REQUEST,
    DiagnosticStatus.QUOTA_EXCEEDED,
    DiagnosticStatus.DAILY_QUOTA_EXHAUSTED,
}


class DiagnosticResult(BaseModel):
    """Structured report schema for direct Gemini diagnostic check."""

    test_name: str = Field(default="gemini_direct_live", description="Diagnostic test identifier")
    model: str = Field(..., description="Target model identifier")
    success: bool = Field(..., description="True if diagnostic succeeded")
    status: DiagnosticStatus = Field(..., description="Granular outcome status")
    http_status: Optional[int] = Field(default=None, description="HTTP/API status code")
    attempts: int = Field(default=1, description="Number of execution attempts performed")
    duration_ms: float = Field(..., description="Total round-trip duration in milliseconds")
    request_id: Optional[str] = Field(default=None, description="Provider request ID if available")
    error_type: Optional[str] = Field(default=None, description="Exception class name")
    error_message: Optional[str] = Field(default=None, description="Sanitized failure message")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    response_text: Optional[str] = Field(default=None, description="Normalized response text")


def sanitize_message(msg: str) -> str:
    """Redact any potential API key or authorization tokens from messages."""
    return SECRET_REDACTION_PATTERN.sub("[REDACTED_SECRET]", msg)


def classify_genai_error(exc: Exception) -> tuple[DiagnosticStatus, Optional[int], str]:
    """Classify Google Gen AI exceptions into standardized diagnostic statuses."""
    exc_str = sanitize_message(str(exc))
    exc_type = type(exc).__name__

    if isinstance(exc, genai_errors.ClientError):
        code = getattr(exc, "code", None)
        if code == 400 or "INVALID_ARGUMENT" in exc_str:
            return DiagnosticStatus.INVALID_REQUEST, code or 400, f"Invalid request parameters: {exc_str}"
        if code in (401, 403):
            if "PERMISSION_DENIED" in exc_str:
                return DiagnosticStatus.PERMISSION_DENIED, code, "Permission denied for this model or API key"
            return (
                DiagnosticStatus.AUTHENTICATION_ERROR,
                code,
                "Authentication failed: invalid or expired Gemini API key",
            )
        if code == 404 or "NOT_FOUND" in exc_str:
            return DiagnosticStatus.MODEL_UNAVAILABLE, code or 404, f"Model not found or unavailable: {exc_str}"
        if code == 429 or "RESOURCE_EXHAUSTED" in exc_str:
            lower = exc_str.lower()
            if any(
                k in lower
                for k in [
                    "generaterequestsperday",
                    "free_tier_requests",
                    "freetier",
                    "requests per day",
                    "per day limit",
                    "retry in 2",
                    "retry in 1",
                ]
            ):
                return (
                    DiagnosticStatus.DAILY_QUOTA_EXHAUSTED,
                    code or 429,
                    "Daily quota exhausted on Google AI Studio Free Tier (20 requests/day). Halting retries immediately.",
                )
            if "quota" in lower:
                return DiagnosticStatus.QUOTA_EXCEEDED, code or 429, "Quota exhausted on Gemini account"
            return (
                DiagnosticStatus.RATE_LIMITED,
                code or 429,
                "Transient rate limit reached on Gemini endpoint (RPM/TPM)",
            )
        return DiagnosticStatus.UNKNOWN_ERROR, code, f"Client error ({code}): {exc_str}"

    if isinstance(exc, genai_errors.ServerError):
        code = getattr(exc, "code", None)
        if code == 503 or "UNAVAILABLE" in exc_str:
            return (
                DiagnosticStatus.SERVICE_UNAVAILABLE,
                code or 503,
                "Gemini service temporarily unavailable (503 high demand spike)",
            )
        if code == 504 or "DEADLINE_EXCEEDED" in exc_str:
            return (
                DiagnosticStatus.REQUEST_TIMEOUT,
                code or 504,
                "Gemini upstream request timed out (504 deadline exceeded)",
            )
        return DiagnosticStatus.SERVICE_UNAVAILABLE, code or 500, f"Upstream Gemini server error ({code}): {exc_str}"

    if "timeout" in exc_str.lower() or "timed out" in exc_str.lower() or "deadline" in exc_str.lower():
        return DiagnosticStatus.REQUEST_TIMEOUT, 408, "Connection to Gemini API timed out"

    if "connection" in exc_str.lower() or "network" in exc_str.lower() or "unreachable" in exc_str.lower():
        return DiagnosticStatus.NETWORK_ERROR, None, "Network failure connecting to Google AI Studio"

    return DiagnosticStatus.UNKNOWN_ERROR, None, f"Unexpected error ({exc_type}): {exc_str}"


def test_direct_gemini_connection(
    settings: Optional[Settings] = None,
    max_attempts: int = 3,
    per_request_timeout: float = 20.0,
    initial_backoff: float = 2.0,
    max_backoff: float = 15.0,
    overall_deadline: float = 60.0,
) -> DiagnosticResult:
    """Execute a direct verification call to Google Gemini with bounded exponential backoff.

    Args:
        settings: Application settings containing credentials.
        max_attempts: Maximum total attempts (default 3: 1 initial + 2 retries).
        per_request_timeout: Network timeout for each HTTP request in seconds.
        initial_backoff: Starting backoff delay in seconds.
        max_backoff: Maximum cap for backoff delay.
        overall_deadline: Total wall-clock budget for the diagnostic check.

    Returns:
        Structured DiagnosticResult with classification and metrics.
    """
    cfg = settings or get_settings()
    model_name = cfg.gemini_model.removeprefix("gemini/")
    api_key = cfg.get_effective_gemini_api_key()

    start_time = time.perf_counter()

    if not api_key:
        return DiagnosticResult(
            model=model_name,
            success=False,
            status=DiagnosticStatus.AUTHENTICATION_ERROR,
            http_status=401,
            attempts=0,
            duration_ms=0.0,
            error_type="ConfigurationError",
            error_message="Gemini API key is missing or not configured.",
        )

    last_status = DiagnosticStatus.UNKNOWN_ERROR
    last_code: Optional[int] = None
    last_msg = ""
    last_exc_type = ""
    attempt = 0

    while attempt < max_attempts:
        attempt += 1
        elapsed = time.perf_counter() - start_time
        if elapsed >= overall_deadline:
            logger.warning("Diagnostic overall deadline (%.1fs) exceeded at attempt %d", overall_deadline, attempt)
            break

        client = None
        try:
            http_options = genai_types.HttpOptions(timeout=int(per_request_timeout * 1000))
            client = genai.Client(api_key=api_key, http_options=http_options)

            response = client.models.generate_content(
                model=model_name,
                contents=DIAGNOSTIC_PROMPT,
            )

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            response_text = (response.text or "").strip()

            return DiagnosticResult(
                model=model_name,
                success=True,
                status=DiagnosticStatus.SUCCESS,
                http_status=200,
                attempts=attempt,
                duration_ms=duration_ms,
                response_text=response_text,
                error_message="Direct Gemini connection successful and verified.",
            )

        except Exception as exc:
            status, code, msg = classify_genai_error(exc)
            last_status = status
            last_code = code
            last_msg = msg
            last_exc_type = type(exc).__name__

            logger.warning(
                "Diagnostic attempt %d/%d failed: status=%s, code=%s, err=%s",
                attempt,
                max_attempts,
                status.value,
                code,
                msg,
            )

            # Fail immediately on non-retryable errors
            if status in NON_RETRYABLE_STATUSES:
                logger.info("Encountered non-retryable error (%s). Halting diagnostic attempts.", status.value)
                break

            # If more attempts remain, sleep with jittered exponential backoff
            if attempt < max_attempts:
                backoff = min(initial_backoff * (2 ** (attempt - 1)), max_backoff)
                jitter = random.uniform(0.1, 0.5)
                sleep_duration = min(backoff + jitter, max(0.1, overall_deadline - (time.perf_counter() - start_time)))
                time.sleep(sleep_duration)

        finally:
            if client is not None and hasattr(client, "close"):
                try:
                    client.close()
                except Exception:
                    pass

    total_duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    return DiagnosticResult(
        model=model_name,
        success=False,
        status=last_status,
        http_status=last_code,
        attempts=attempt,
        duration_ms=total_duration_ms,
        error_type=last_exc_type,
        error_message=last_msg,
    )
