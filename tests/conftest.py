"""Shared pytest fixtures for Site DNA test suite."""

from typing import Generator

import pytest
from fastapi.testclient import TestClient

from site_dna.api.main import create_app
from site_dna.core.config import Settings


@pytest.fixture
def mock_env_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure clean environment with no real API keys present."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("APP_NAME", "Site DNA Test")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ENABLE_LIVE_LLM_TESTS", "false")


@pytest.fixture
def test_settings_with_key() -> Settings:
    """Return Settings instance with a dummy test key configured."""
    return Settings(
        app_name="Site DNA Test",
        app_env="test",
        gemini_api_key="test_dummy_key_1234567890",
        gemini_model="gemini-3.6-flash",
        log_level="DEBUG",
        enable_live_llm_tests=False,
    )


@pytest.fixture
def test_settings_no_key() -> Settings:
    """Return Settings instance with no key configured."""
    return Settings(
        app_name="Site DNA Test",
        app_env="test",
        gemini_api_key=None,
        gemini_model="gemini-3.6-flash",
        log_level="INFO",
        enable_live_llm_tests=False,
    )


@pytest.fixture
def client(test_settings_with_key: Settings) -> Generator[TestClient, None, None]:
    """TestClient configured with dummy test settings."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
