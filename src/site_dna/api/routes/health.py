"""Health and readiness routes for Site DNA."""

from fastapi import APIRouter, Depends, Response, status

from site_dna.core.config import Settings, get_settings
from site_dna.schemas.health import (
    HealthResponse,
    ReadinessCheckDetails,
    ReadinessResponse,
)

router = APIRouter(prefix="/api/v1", tags=["Health & Readiness"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Basic service health check",
    description="Returns HTTP 200 if the FastAPI application is alive, regardless of LLM credentials.",
)
async def health_check() -> HealthResponse:
    """Return basic health status of the running service."""
    return HealthResponse(
        status="ok",
        service="site-dna",
        version="0.1.0",
        phase="01",
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness check for LLM operations",
    description=(
        "Reports configuration readiness for AI operations without making "
        "expensive or billable network calls. Returns HTTP 503 if API keys are missing."
    ),
    responses={
        status.HTTP_200_OK: {"description": "Service is ready for operations"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Configuration missing or unready"},
    },
)
async def readiness_check(
    response: Response,
    settings: Settings = Depends(get_settings),
) -> ReadinessResponse:
    """Check readiness of configuration without invoking external LLM network requests."""
    key_configured = settings.is_gemini_configured()

    details = ReadinessCheckDetails(
        backend_running=True,
        api_key_configured=key_configured,
        model_configured=settings.gemini_model,
        live_connectivity_verified=False,  # Offline check; does not hit paid network endpoints
        environment=settings.app_env,
    )

    if not key_configured:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadinessResponse(
            status="unready",
            service="site-dna",
            version="0.1.0",
            ready=False,
            details=details,
            message=(
                "Gemini API key is not configured. Set GEMINI_API_KEY in .env "
                "or system environment before running live AI tasks."
            ),
        )

    response.status_code = status.HTTP_200_OK
    return ReadinessResponse(
        status="ready",
        service="site-dna",
        version="0.1.0",
        ready=True,
        details=details,
        message="Service configuration is complete and ready for operations.",
    )
