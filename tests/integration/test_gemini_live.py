"""Live integration tests against Google Gemini 3.8 Flash.

These tests are skipped by default to prevent accidental paid token consumption.
They require:
1. ENABLE_LIVE_LLM_TESTS=true in environment or .env
2. A valid GEMINI_API_KEY configured.
"""

import os

import pytest

from site_dna.core.config import get_settings
from site_dna.services.gemini_diagnostics import (
    DiagnosticStatus,
)
from site_dna.services.gemini_diagnostics import (
    test_direct_gemini_connection as run_direct_gemini_diagnostic,
)

settings = get_settings()
LIVE_ENABLED = os.getenv("ENABLE_LIVE_LLM_TESTS", "").lower() in ("true", "1", "yes") or settings.enable_live_llm_tests
KEY_AVAILABLE = settings.is_gemini_configured()

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not (LIVE_ENABLED and KEY_AVAILABLE),
        reason="Live integration tests require ENABLE_LIVE_LLM_TESTS=true and a valid GEMINI_API_KEY",
    ),
]


def test_live_direct_gemini_diagnostic():
    """Execute live direct Google GenAI connection to gemini-3.6-flash."""
    result = run_direct_gemini_diagnostic(
        settings=settings,
        max_attempts=2,
        per_request_timeout=15.0,
    )

    # If upstream is experiencing high demand (503/504) or quota exhaustion (429), report as skipped/blocked
    if result.status in (
        DiagnosticStatus.SERVICE_UNAVAILABLE,
        DiagnosticStatus.REQUEST_TIMEOUT,
        DiagnosticStatus.DAILY_QUOTA_EXHAUSTED,
    ):
        pytest.skip(f"Live Gemini endpoint temporarily unavailable or quota exhausted: {result.error_message}")

    assert result.success is True, f"Live Gemini check failed: {result.error_message} ({result.error_type})"
    assert result.response_text is not None
    assert result.duration_ms > 0


def test_live_crewai_agent_execution():
    """Execute live CrewAI task using the Foundation Smoke Agent."""
    from site_dna.agents.smoke_agent import run_smoke_crew

    try:
        agent_output = run_smoke_crew()
        assert agent_output.project == "Site DNA"
        assert "operational" in agent_output.status.lower()
    except Exception as exc:
        err_msg = str(exc)
        if any(token in err_msg for token in ("503", "504", "UNAVAILABLE", "DEADLINE_EXCEEDED", "high demand", "429", "RESOURCE_EXHAUSTED", "quota")):
            pytest.skip(f"Live CrewAI task blocked by upstream capacity: {exc}")
        raise
