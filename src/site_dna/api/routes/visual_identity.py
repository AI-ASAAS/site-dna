"""FastAPI route for AI Visual Identity Analysis."""

import re
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from site_dna.analysis.visual_identity.context_builder import ContextValidationError
from site_dna.analysis.visual_identity.service import VisualIdentityAnalysisService
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.visual_identity import (
    VisualIdentityAnalysisRequest,
    VisualIdentityReport,
)

logger = get_logger("api.routes.visual_identity")

router = APIRouter(prefix="/api/v1/analysis", tags=["Visual Analysis"])


def verify_visual_analysis_access(
    request: Request,
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    """Validate that visual analysis API is enabled, local, and authenticated."""
    # Gate 1: Enabled flag
    if not settings.visual_analysis_api_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Visual analysis API is disabled. Set VISUAL_ANALYSIS_API_ENABLED=true in configuration.",
        )

    # Gate 2: Localhost check in development
    if settings.app_env == "development":
        client_host = request.client.host if request.client else ""
        if client_host not in ("127.0.0.1", "::1", "localhost", "testclient"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Visual analysis API only accepts loopback requests in development mode, got '{client_host}'.",
            )

    # Gate 3: Bearer token verification if configured
    if settings.visual_analysis_api_token and settings.visual_analysis_api_token.get_secret_value().strip():
        expected_token = settings.visual_analysis_api_token.get_secret_value().strip()
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
                detail="Invalid visual analysis API authorization token.",
                headers={"WWW-Authenticate": "Bearer"},
            )


@router.post(
    "/visual-identity",
    response_model=VisualIdentityReport,
    status_code=status.HTTP_200_OK,
    summary="Execute multimodal visual identity analysis on visual evidence",
    dependencies=[Depends(verify_visual_analysis_access)],
)
async def analyze_visual_identity(
    request_data: VisualIdentityAnalysisRequest,
    settings: Settings = Depends(get_settings),
) -> VisualIdentityReport:
    """Execute AI multimodal visual identity analysis on previously captured visual artifacts."""
    logger.info(
        "Received visual identity analysis request: run_id=%s, file=%s",
        request_data.visual_run_id,
        request_data.visual_manifest_file,
    )

    # Validate inputs against path traversal
    if request_data.visual_manifest_file:
        manifest_path = Path(request_data.visual_manifest_file)
        if ".." in manifest_path.parts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Path traversal detected in visual_manifest_file.",
            )
    elif request_data.visual_run_id:
        if not re.match(r"^[a-zA-Z0-9_\-]+$", request_data.visual_run_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid characters in visual_run_id.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify either visual_run_id or visual_manifest_file.",
        )

    try:
        service = VisualIdentityAnalysisService(settings=settings)
        report = service.analyze_visual_identity(request_data)
        return report
    except (FileNotFoundError, ContextValidationError) as exc:
        logger.warning("Visual artifact not found: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Visual artifact not found: {exc}",
        )
    except ValueError as exc:
        logger.warning("Invalid request or artifact: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Visual analysis execution failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Visual analysis processing failed internally.",
        )
