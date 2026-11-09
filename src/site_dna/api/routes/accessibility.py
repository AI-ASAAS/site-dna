"""FastAPI routes for Site DNA Phase 10 — Web Accessibility & WCAG 2.2 Intelligence."""

import json
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from site_dna.analysis.accessibility.service import AccessibilityService
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.accessibility import (
    AccessibilityAnalysisRequest,
    AccessibilityReport,
)

logger = get_logger("api.routes.accessibility")
router = APIRouter(prefix="/api/v1/analysis/accessibility", tags=["Accessibility & WCAG Intelligence"])


def get_accessibility_service(settings: Settings = Depends(get_settings)) -> AccessibilityService:
    """Dependency provider for AccessibilityService."""
    return AccessibilityService(settings=settings)


def verify_accessibility_auth(
    authorization: Optional[str] = Header(None),
    settings: Settings = Depends(get_settings),
) -> None:
    """Optional bearer token verification for Accessibility API."""
    token = settings.get_effective_accessibility_token()
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
            detail="Invalid Accessibility Intelligence API bearer token.",
        )


class AccessibilityTriggerPayload(BaseModel):
    """Payload for POST /api/v1/analysis/accessibility."""

    crawl_run_id: str = Field(..., description="ID of completed discovery crawl run")
    visual_run_id: Optional[str] = Field(None, description="Optional ID of visual capture run")
    ux_run_id: Optional[str] = Field(None, description="Optional ID of UX/UI run")
    language: str = Field(default="ar", description="Language ('ar' or 'en')")
    max_pages: int = Field(default=8, ge=1, le=50, description="Max representative pages to evaluate")
    deterministic_only: bool = Field(default=False, description="Run deterministic checks only")
    include_automated_rules: bool = Field(default=True, description="Run automated rules engine")


class UpdateManualReviewPayload(BaseModel):
    """Payload for updating manual review task outcome."""

    status: str = Field(..., description="Review outcome status")
    notes: Optional[str] = Field(None, description="Reviewer observations and notes")
    reviewer: Optional[str] = Field(None, description="Reviewer identity or name")


@router.post(
    "",
    response_model=AccessibilityReport,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_accessibility_auth)],
)
async def trigger_accessibility_analysis(
    payload: AccessibilityTriggerPayload,
    service: AccessibilityService = Depends(get_accessibility_service),
    settings: Settings = Depends(get_settings),
) -> AccessibilityReport:
    """Execute a passive Accessibility & WCAG 2.2 audit on a previous crawl run."""
    if not settings.accessibility_analysis_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accessibility analysis engine is disabled in configuration.",
        )

    req = AccessibilityAnalysisRequest(
        crawl_run_id=payload.crawl_run_id,
        visual_run_id=payload.visual_run_id,
        ux_run_id=payload.ux_run_id,
        language=payload.language,
        max_pages=payload.max_pages,
        deterministic_only=payload.deterministic_only,
        include_automated_rules=payload.include_automated_rules,
        save_results=True,
    )

    try:
        report = await service.analyze_accessibility(req)
        return report
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        logger.error("Accessibility analysis failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Accessibility audit failed: {e}"
        ) from e


@router.get(
    "/{crawl_run_id}",
    response_model=dict[str, Any],
    dependencies=[Depends(verify_accessibility_auth)],
)
async def get_accessibility_report(
    crawl_run_id: str,
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Retrieve saved accessibility report for a given crawl run."""
    runs_dir = Path("runs")
    a11y_base = runs_dir / crawl_run_id / "analysis" / "accessibility"

    if not a11y_base.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No accessibility analysis found for crawl_run_id: '{crawl_run_id}'",
        )

    subdirs = [d for d in a11y_base.iterdir() if d.is_dir()]
    if not subdirs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No accessibility run records found under: '{crawl_run_id}'",
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
    "/{crawl_run_id}/wcag",
    response_model=list[dict[str, Any]],
    dependencies=[Depends(verify_accessibility_auth)],
)
async def get_wcag_criteria_breakdown(
    crawl_run_id: str,
    settings: Settings = Depends(get_settings),
) -> list[dict[str, Any]]:
    """Retrieve mapped WCAG 2.2 criteria list for a crawl run."""
    runs_dir = Path("runs")
    a11y_base = runs_dir / crawl_run_id / "analysis" / "accessibility"

    if not a11y_base.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No accessibility data found.")

    subdirs = [d for d in a11y_base.iterdir() if d.is_dir()]
    if not subdirs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No accessibility records found.")

    latest_dir = sorted(subdirs, key=lambda d: d.stat().st_mtime, reverse=True)[0]
    wcag_file = latest_dir / "wcag-criteria.json"
    if not wcag_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="wcag-criteria.json missing.")

    return json.loads(wcag_file.read_text(encoding="utf-8"))


@router.post(
    "/{crawl_run_id}/tasks/{review_id}",
    response_model=dict[str, Any],
    dependencies=[Depends(verify_accessibility_auth)],
)
async def update_manual_review_task(
    crawl_run_id: str,
    review_id: str,
    payload: UpdateManualReviewPayload,
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Record human reviewer decision and notes for a specific manual review task."""
    runs_dir = Path("runs")
    a11y_base = runs_dir / crawl_run_id / "analysis" / "accessibility"
    if not a11y_base.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No accessibility run found.")

    subdirs = [d for d in a11y_base.iterdir() if d.is_dir()]
    if not subdirs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No run records found.")

    latest_dir = sorted(subdirs, key=lambda d: d.stat().st_mtime, reverse=True)[0]
    tasks_file = latest_dir / "manual-review-tasks.json"
    analysis_file = latest_dir / "analysis.json"
    if not tasks_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="manual-review-tasks.json missing.")

    try:
        tasks = json.loads(tasks_file.read_text(encoding="utf-8"))
        updated = False
        for t in tasks:
            if t.get("review_id") == review_id:
                t["review_status"] = payload.status
                t["reviewer_notes"] = payload.notes
                if payload.reviewer:
                    t["reviewer"] = payload.reviewer
                from datetime import datetime, timezone

                t["reviewed_at"] = datetime.now(timezone.utc).isoformat()
                updated = True
                break

        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{review_id}' not found.")

        tasks_file.write_text(json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8")

        # Also sync back to analysis.json if present
        if analysis_file.exists():
            adata = json.loads(analysis_file.read_text(encoding="utf-8"))
            adata["manual_review_tasks"] = tasks
            analysis_file.write_text(json.dumps(adata, indent=2, ensure_ascii=False), encoding="utf-8")

        return {
            "status": payload.status,
            "review_id": review_id,
            "reviewer": payload.reviewer,
            "notes": payload.notes,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update manual task: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
