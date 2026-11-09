"""FastAPI routes for Site DNA Phase 09 — Security, Privacy & Trust Intelligence."""

import json
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from site_dna.analysis.security_privacy.service import SecurityPrivacyService
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.security_privacy import (
    SecurityPrivacyAnalysisRequest,
    SecurityPrivacyReport,
)

logger = get_logger("api.routes.security_privacy")
router = APIRouter(prefix="/api/v1/analysis/security-privacy", tags=["Security & Privacy Intelligence"])


def get_security_service(settings: Settings = Depends(get_settings)) -> SecurityPrivacyService:
    """Dependency provider for SecurityPrivacyService."""
    return SecurityPrivacyService(settings=settings)


def verify_security_auth(
    authorization: Optional[str] = Header(None),
    settings: Settings = Depends(get_settings),
) -> None:
    """Optional bearer token verification for Security API."""
    token = settings.get_effective_security_token()
    if not token:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header.",
        )
    provided = authorization.removeprefix("Bearer ").strip()
    if provided != token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Security Intelligence API bearer token.",
        )


class SecurityTriggerPayload(BaseModel):
    """Payload for POST /api/v1/analysis/security-privacy."""

    crawl_run_id: str = Field(..., description="ID of completed discovery crawl run")
    visual_run_id: Optional[str] = Field(None, description="Optional ID of visual capture run")
    language: str = Field(default="ar", description="Language ('ar' or 'en')")
    max_pages: int = Field(default=8, ge=1, le=50, description="Max pages to assess")
    deterministic_only: bool = Field(default=False, description="Run deterministic checks only")


@router.post(
    "",
    response_model=SecurityPrivacyReport,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_security_auth)],
)
async def trigger_security_analysis(
    payload: SecurityTriggerPayload,
    service: SecurityPrivacyService = Depends(get_security_service),
    settings: Settings = Depends(get_settings),
) -> SecurityPrivacyReport:
    """Execute a passive Security, Privacy & Trust audit on a previous crawl run."""
    if not settings.security_analysis_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Security & Privacy analysis engine is disabled in configuration.",
        )

    req = SecurityPrivacyAnalysisRequest(
        crawl_run_id=payload.crawl_run_id,
        visual_run_id=payload.visual_run_id,
        language=payload.language,
        max_pages=payload.max_pages,
        deterministic_only=payload.deterministic_only,
        save_results=True,
    )

    try:
        report = await service.analyze_security(req)
        return report
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        logger.error("Security analysis failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Security audit failed: {e}"
        ) from e


@router.get(
    "/{crawl_run_id}",
    response_model=dict[str, Any],
    dependencies=[Depends(verify_security_auth)],
)
async def get_security_report(
    crawl_run_id: str,
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Retrieve saved security report for a given crawl run."""
    runs_dir = Path("runs")
    sec_base = runs_dir / crawl_run_id / "analysis" / "security-privacy"

    if not sec_base.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No security analysis found for crawl_run_id: '{crawl_run_id}'",
        )

    subdirs = [d for d in sec_base.iterdir() if d.is_dir()]
    if not subdirs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No security analysis records found under: '{crawl_run_id}'",
        )

    latest_dir = sorted(subdirs, key=lambda d: d.stat().st_mtime, reverse=True)[0]
    analysis_file = latest_dir / "analysis.json"
    if not analysis_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="analysis.json missing.")

    try:
        return json.loads(analysis_file.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to read report: {e}"
        ) from e


@router.get(
    "/{crawl_run_id}/headers",
    response_model=dict[str, Any],
    dependencies=[Depends(verify_security_auth)],
)
async def get_security_headers_breakdown(
    crawl_run_id: str,
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Retrieve HTTP security headers breakdown for a crawl run."""
    runs_dir = Path("runs")
    sec_base = runs_dir / crawl_run_id / "analysis" / "security-privacy"

    if not sec_base.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No security data found.")

    subdirs = [d for d in sec_base.iterdir() if d.is_dir()]
    if not subdirs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No security run records found.")

    latest_dir = sorted(subdirs, key=lambda d: d.stat().st_mtime, reverse=True)[0]
    hdr_file = latest_dir / "security-headers.json"
    if not hdr_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="security-headers.json missing.")

    return json.loads(hdr_file.read_text(encoding="utf-8"))
