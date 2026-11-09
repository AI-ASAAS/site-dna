"""Unit tests for configuration management and credential safety."""

import pytest
from pydantic import ValidationError

from site_dna.core.config import Settings


def test_default_config_loads(monkeypatch: pytest.MonkeyPatch):
    """Verify that default settings load with anticipated defaults."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    settings = Settings(
        _env_file=None,
        app_name="Site DNA",
        app_env="development",
        app_host="127.0.0.1",
        app_port=8000,
        gemini_model="gemini-3.6-flash",
        gemini_api_key=None,
        log_level="INFO",
    )
    assert settings.app_name == "Site DNA"
    assert settings.app_env == "development"
    assert settings.app_host == "127.0.0.1"
    assert settings.app_port == 8000
    assert settings.gemini_model == "gemini-3.6-flash"
    assert settings.log_level == "INFO"
    assert settings.is_gemini_configured() is False


def test_custom_values_override():
    """Verify that explicitly passed values override defaults."""
    settings = Settings(
        app_name="Custom Site DNA",
        app_env="production",
        app_host="0.0.0.0",
        app_port=9000,
        gemini_model="gemini-3.6-flash",
        gemini_api_key="secret-key-12345",
        log_level="DEBUG",
    )
    assert settings.app_name == "Custom Site DNA"
    assert settings.app_port == 9000
    assert settings.is_gemini_configured() is True
    assert settings.get_effective_gemini_api_key() == "secret-key-12345"


def test_secrets_do_not_appear_in_repr():
    """Verify that secret values are completely masked in string and repr output."""
    raw_secret = "MOCK_SuperSecretKey123456789"
    settings = Settings(gemini_api_key=raw_secret)

    repr_str = repr(settings)
    str_val = str(settings)

    assert raw_secret not in repr_str
    assert raw_secret not in str_val
    assert "[configured]" in repr_str


def test_empty_and_whitespace_key_handling():
    """Verify that empty or whitespace-only keys are treated as unconfigured."""
    settings_empty = Settings(gemini_api_key="")
    assert settings_empty.is_gemini_configured() is False
    assert settings_empty.get_effective_gemini_api_key() is None

    settings_spaces = Settings(gemini_api_key="   ")
    assert settings_spaces.is_gemini_configured() is False
    assert settings_spaces.get_effective_gemini_api_key() is None


def test_credential_precedence_gemini_over_google(monkeypatch: pytest.MonkeyPatch):
    """Verify that GEMINI_API_KEY takes precedence over GOOGLE_API_KEY."""
    monkeypatch.setenv("GOOGLE_API_KEY", "fallback_google_key_9999")
    settings = Settings(gemini_api_key="primary_gemini_key_1111")

    assert settings.get_effective_gemini_api_key() == "primary_gemini_key_1111"

    # When GEMINI_API_KEY is omitted, fallback should resolve
    settings_no_gemini = Settings(gemini_api_key=None)
    assert settings_no_gemini.get_effective_gemini_api_key() == "fallback_google_key_9999"


def test_invalid_log_level_rejected():
    """Verify that an unsupported log level raises validation error."""
    with pytest.raises(ValidationError):
        Settings(log_level="INVALID_LEVEL")


def test_invalid_port_rejected():
    """Verify that ports outside [1, 65535] are rejected."""
    with pytest.raises(ValidationError):
        Settings(app_port=70000)

    with pytest.raises(ValidationError):
        Settings(app_port=-1)
