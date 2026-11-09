"""FastAPI route for Technical SEO, Performance, and Core Web Vitals Analysis."""

import re

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from site_dna.analysis.technical_seo.context_builder import TechnicalSEOContextValidationError
from site_dna.analysis.technical_seo.service import TechnicalSEOAnalysisService
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.technical_seo import (
    TechnicalSEOAnalysisRequest,
    TechnicalSEOReport,
)

logger = get_logger("api.routes.technical_seo")

router = APIRouter(prefix="/api/v1/analysis", tags=["Technical SEO & Performance"])


def verify_technical_seo_access(
    request: Request,
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    """Validate that Technical SEO analysis API is enabled, local, and authenticated."""
    # Gate 1: Enabled flag
    if not settings.technical_seo_api_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Technical SEO analysis API is disabled. Set TECHNICAL_SEO_API_ENABLED=true in configuration.",
        )

    # Gate 2: Localhost check in development
    if settings.app_env == "development":
        client_host = request.client.host if request.client else ""
        if client_host not in ("127.0.0.1", "::1", "localhost", "testclient"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Technical SEO analysis API only accepts loopback requests in development mode, got '{client_host}'.",
            )

    # Gate 3: Bearer token verification if configured
    if settings.technical_seo_api_token and settings.technical_seo_api_token.get_secret_value().strip():
        expected_token = settings.technical_seo_api_token.get_secret_value().strip()
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or malformed Authorization header. Bearer token required.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = authorization.split("Bearer ", 1)[1].strip()
        if token != expected_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Technical SEO analysis API authorization token.",
                headers={"WWW-Authenticate": "Bearer"},
            )


@router.post(
    "/technical-seo",
    response_model=TechnicalSEOReport,
    status_code=status.HTTP_200_OK,
    summary="Execute Technical SEO & Performance Audit (Phase 07)",
    description=(
        "Audits crawlability, indexability, canonical tags, XML sitemaps, metadata, "
        "structured data, JavaScript/mobile rendering parity, and Core Web Vitals performance."
    ),
    dependencies=[Depends(verify_technical_seo_access)],
)
async def analyze_technical_seo(
    request_body: TechnicalSEOAnalysisRequest,
    settings: Settings = Depends(get_settings),
) -> TechnicalSEOReport:
    """Run Technical SEO and performance analysis on existing crawl results."""
    # Security check: Identifier format and path traversal prevention
    if not re.match(r"^[a-zA-Z0-9_\-]+$", request_body.crawl_run_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path traversal or invalid crawl_run_id format: '{request_body.crawl_run_id}'.",
        )

    if request_body.visual_run_id and not re.match(r"^[a-zA-Z0-9_\-]+$", request_body.visual_run_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path traversal or invalid visual_run_id format: '{request_body.visual_run_id}'.",
        )

    logger.info("API received Technical SEO analysis request for crawl_run_id=%s", request_body.crawl_run_id)

    try:
        service = TechnicalSEOAnalysisService(settings=settings)
        report = service.analyze(request_body)
        return report

    except TechnicalSEOContextValidationError as exc:
        logger.warning("Technical SEO validation error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crawl artifacts not found or invalid: {exc}",
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error during Technical SEO analysis: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Technical SEO analysis failed: {type(exc).__name__}: {str(exc)}",
        ) from exc
