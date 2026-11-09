"""Unit tests for the CrewAI LLM factory and Gemini integration."""

from unittest.mock import MagicMock, patch

import pytest

from site_dna.core.config import Settings
from site_dna.core.llm import (
    GeminiConfigurationError,
    format_crewai_gemini_model,
    get_llm,
)


def test_format_crewai_gemini_model_adds_prefix():
    """Verify that 'gemini/' prefix is added when missing."""
    assert format_crewai_gemini_model("gemini-3.6-flash") == "gemini/gemini-3.6-flash"


def test_format_crewai_gemini_model_preserves_existing_prefix():
    """Verify that existing 'gemini/' prefix is preserved without duplication."""
    assert format_crewai_gemini_model("gemini/gemini-3.6-flash") == "gemini/gemini-3.6-flash"


def test_format_crewai_gemini_model_rejects_empty():
    """Verify that empty string raises GeminiConfigurationError."""
    with pytest.raises(GeminiConfigurationError):
        format_crewai_gemini_model("")


def test_get_llm_raises_when_key_missing(test_settings_no_key: Settings):
    """Verify that get_llm raises GeminiConfigurationError when no key is provided."""
    with pytest.raises(GeminiConfigurationError) as exc_info:
        get_llm(settings=test_settings_no_key)
    assert "GEMINI_API_KEY is not configured" in str(exc_info.value)


@patch("site_dna.core.llm.LLM")
def test_get_llm_configures_native_gemini(mock_crewai_llm: MagicMock, test_settings_with_key: Settings):
    """Verify that get_llm instantiates CrewAI LLM targeting gemini/gemini-3.6-flash."""
    mock_instance = MagicMock()
    mock_crewai_llm.return_value = mock_instance

    llm = get_llm(settings=test_settings_with_key, timeout=45)

    mock_crewai_llm.assert_called_once_with(
        model="gemini/gemini-3.6-flash",
        api_key="test_dummy_key_1234567890",
        timeout=45,
    )
    assert llm == mock_instance


@patch("site_dna.core.llm.LLM")
def test_get_llm_supports_explicit_overrides(mock_crewai_llm: MagicMock):
    """Verify that get_llm supports explicit model and api_key overrides."""
    get_llm(model="gemini-3.6-flash", api_key="override_key", timeout=120)

    mock_crewai_llm.assert_called_once_with(
        model="gemini/gemini-3.6-flash",
        api_key="override_key",
        timeout=120,
    )
