"""FastAPI route for AI Content & Marketing Intelligence Analysis."""

import re

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from site_dna.analysis.content_marketing.context_builder import ContentContextValidationError
from site_dna.analysis.content_marketing.service import ContentMarketingAnalysisService
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.content_marketing import (
    ContentAnalysisRequest,
    ContentMarketingReport,
)

logger = get_logger("api.routes.content_marketing")

router = APIRouter(prefix="/api/v1/analysis", tags=["Content & Marketing Intelligence"])


def verify_content_analysis_access(
    request: Request,
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    """Validate that Content Marketing analysis API is enabled, local, and authenticated."""
    # Gate 1: Enabled flag
    if not settings.content_analysis_api_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Content analysis API is disabled. Set CONTENT_ANALYSIS_API_ENABLED=true in configuration.",
        )

    # Gate 2: Localhost check in development
    if settings.app_env == "development":
        client_host = request.client.host if request.client else ""
        if client_host not in ("127.0.0.1", "::1", "localhost", "testclient"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Content analysis API only accepts loopback requests in development mode, got '{client_host}'.",
            )

    # Gate 3: Bearer token verification if configured
    if settings.content_analysis_api_token and settings.content_analysis_api_token.get_secret_value().strip():
        expected_token = settings.content_analysis_api_token.get_secret_value().strip()
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
                detail="Invalid Content analysis API authorization token.",
                headers={"WWW-Authenticate": "Bearer"},
            )


@router.post(
    "/content-marketing",
    response_model=ContentMarketingReport,
    status_code=status.HTTP_200_OK,
    summary="Execute Content & Marketing Intelligence audit on crawl evidence",
    dependencies=[Depends(verify_content_analysis_access)],
)
async def analyze_content_marketing(
    request_data: ContentAnalysisRequest,
    settings: Settings = Depends(get_settings),
) -> ContentMarketingReport:
    """Execute AI and deterministic Content & Marketing audit on previously captured crawl artifacts."""
    logger.info(
        "Received Content Marketing analysis request: crawl_run_id=%s, visual_run_id=%s",
        request_data.crawl_run_id,
        request_data.visual_run_id,
    )

    # Validate inputs against path traversal
    if not request_data.crawl_run_id or not re.match(r"^[a-zA-Z0-9_\-]+$", request_data.crawl_run_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path traversal detected or invalid crawl_run_id format.",
        )
    if request_data.visual_run_id and not re.match(r"^[a-zA-Z0-9_\-]+$", request_data.visual_run_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid characters in visual_run_id.",
        )

    try:
        service = ContentMarketingAnalysisService(settings=settings)
        report = service.analyze(request_data, offline_mode=request_data.offline_mode)
        return report
    except (FileNotFoundError, ContentContextValidationError) as exc:
        logger.warning("Crawl artifact not found for content analysis: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crawl artifact not found: {exc}",
        )
    except ValueError as exc:
        logger.warning("Invalid request or artifact: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Content analysis execution failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content analysis processing failed internally.",
        )
