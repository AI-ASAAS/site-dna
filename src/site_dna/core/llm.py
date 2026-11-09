"""LLM Factory and integration layer for Google Gemini and CrewAI."""

from typing import Optional

from crewai import LLM

from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger

logger = get_logger(__name__)


class GeminiConfigurationError(Exception):
    """Raised when Gemini LLM configuration or credentials are invalid or missing."""


def format_crewai_gemini_model(model_name: str) -> str:
    """Format model identifier with CrewAI's required 'gemini/' provider prefix without duplication."""
    stripped = model_name.strip()
    if not stripped:
        raise GeminiConfigurationError("Model identifier cannot be empty")
    if stripped.startswith("gemini/"):
        return stripped
    return f"gemini/{stripped}"


def get_llm(
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout: int = 60,
    settings: Optional[Settings] = None,
) -> LLM:
    """Create and return a configured CrewAI LLM instance targeting Gemini 3.8 Flash.

    Args:
        model: Optional model override. Defaults to settings.gemini_model.
        api_key: Optional API key override. Defaults to effective key in settings.
        timeout: Network timeout in seconds (default 60).
        settings: Optional Settings instance. Defaults to singleton get_settings().

    Returns:
        Configured CrewAI LLM instance.

    Raises:
        GeminiConfigurationError: If API key is missing or model is invalid.
    """
    cfg = settings or get_settings()

    target_model = model or cfg.gemini_model
    effective_key = api_key or cfg.get_effective_gemini_api_key()

    if not effective_key:
        raise GeminiConfigurationError(
            "GEMINI_API_KEY is not configured. "
            "Please provide a valid key via .env file or GEMINI_API_KEY environment variable. "
            "Get an API key at https://aistudio.google.com/."
        )

    formatted_model = format_crewai_gemini_model(target_model)
    logger.debug("Configuring CrewAI LLM with model: %s (timeout=%ds)", formatted_model, timeout)

    # Instantiate CrewAI LLM targeting Gemini natively without falling back to OpenAI
    llm_instance = LLM(
        model=formatted_model,
        api_key=effective_key,
        timeout=timeout,
    )

    return llm_instance
