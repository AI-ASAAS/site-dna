"""FastAPI route for AI UX/UI Usability Intelligence Analysis."""

import re
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from site_dna.analysis.ux_ui.context_builder import UXContextValidationError
from site_dna.analysis.ux_ui.service import UXAnalysisService
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.ux_ui import (
    UXAnalysisRequest,
    UXReport,
)

logger = get_logger("api.routes.ux_ui")

router = APIRouter(prefix="/api/v1/analysis", tags=["UX/UI Analysis"])


def verify_ux_analysis_access(
    request: Request,
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    """Validate that UX analysis API is enabled, local, and authenticated."""
    # Gate 1: Enabled flag
    if not settings.ux_analysis_api_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="UX/UI analysis API is disabled. Set UX_ANALYSIS_API_ENABLED=true in configuration.",
        )

    # Gate 2: Localhost check in development
    if settings.app_env == "development":
        client_host = request.client.host if request.client else ""
        if client_host not in ("127.0.0.1", "::1", "localhost", "testclient"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"UX/UI analysis API only accepts loopback requests in development mode, got '{client_host}'.",
            )

    # Gate 3: Bearer token verification if configured
    if settings.ux_analysis_api_token and settings.ux_analysis_api_token.get_secret_value().strip():
        expected_token = settings.ux_analysis_api_token.get_secret_value().strip()
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
                detail="Invalid UX/UI analysis API authorization token.",
                headers={"WWW-Authenticate": "Bearer"},
            )


@router.post(
    "/ux-ui",
    response_model=UXReport,
    status_code=status.HTTP_200_OK,
    summary="Execute UX/UI and usability intelligence analysis on visual evidence",
    dependencies=[Depends(verify_ux_analysis_access)],
)
async def analyze_ux_ui(
    request_data: UXAnalysisRequest,
    settings: Settings = Depends(get_settings),
) -> UXReport:
    """Execute AI and deterministic UX/UI usability analysis on previously captured visual artifacts."""
    logger.info(
        "Received UX/UI analysis request: run_id=%s, file=%s",
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
        service = UXAnalysisService(settings=settings)
        report = service.analyze_ux(request_data, offline_mode=request_data.offline_mode)
        return report
    except (FileNotFoundError, UXContextValidationError) as exc:
        logger.warning("Visual artifact not found for UX analysis: %s", exc)
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
        logger.error("UX/UI analysis execution failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="UX/UI analysis processing failed internally.",
        )
