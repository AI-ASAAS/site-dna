"""FastAPI routes for Site DNA Phase 11 — Strategic Intelligence & Unified Action Roadmap."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from site_dna.analysis.strategic_intelligence.service import StrategicIntelligenceService
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.strategic_intelligence import (
    ActionStatus,
    StrategicAnalysisRequest,
    StrategicIntelligenceReport,
)

logger = get_logger("api.routes.strategic_intelligence")
router = APIRouter(prefix="/api/v1/analysis/strategy", tags=["Strategic Intelligence & Action Roadmap"])

_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]+$")


def validate_id_str(val: str, field_name: str = "ID") -> None:
    if not val or not _ID_REGEX.match(val):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name} format: '{val}'. Only alphanumeric and hyphens allowed.",
        )


def get_strategic_service(settings: Settings = Depends(get_settings)) -> StrategicIntelligenceService:
    return StrategicIntelligenceService(settings=settings)


def verify_strategic_auth(
    authorization: Optional[str] = Header(None),
    settings: Settings = Depends(get_settings),
) -> None:
    token = getattr(settings, "strategic_analysis_token", None)
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
            detail="Invalid Strategic Intelligence API bearer token.",
        )


class StrategicTriggerPayload(BaseModel):
    """Payload for POST /api/v1/analysis/strategy."""

    crawl_run_id: str = Field(..., description="ID of completed discovery crawl run")
    source_run_ids: Optional[dict[str, str]] = Field(None, description="Optional explicit run IDs per phase")
    language: str = Field(default="ar", description="Language ('ar' or 'en')")
    max_actions: int = Field(default=50, ge=5, le=200)
    deterministic_only: bool = Field(default=False)


class UpdateActionStatusPayload(BaseModel):
    """Payload for updating an action backlog status."""

    status: ActionStatus = Field(..., description="New execution status")
    notes: Optional[str] = Field(None, description="Reviewer or operator notes")
    reviewer: Optional[str] = Field(None, description="Reviewer name or identifier")

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, val: Any) -> Any:
        if isinstance(val, str):
            s = val.strip().lower()
            mapping = {
                "verified": "verified_completed",
                "completed": "verified_completed",
                "pending": "proposed",
            }
            return mapping.get(s, s)
        return val


@router.post(
    "",
    response_model=StrategicIntelligenceReport,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_strategic_auth)],
)
async def trigger_strategic_analysis(
    payload: StrategicTriggerPayload,
    service: StrategicIntelligenceService = Depends(get_strategic_service),
    settings: Settings = Depends(get_settings),
) -> StrategicIntelligenceReport:
    """Execute cross-agent synthesis and generate prioritized roadmap."""
    validate_id_str(payload.crawl_run_id, "crawl_run_id")

    req = StrategicAnalysisRequest(
        crawl_run_id=payload.crawl_run_id,
        source_run_ids=payload.source_run_ids,
        language=payload.language,
        max_actions=payload.max_actions,
        deterministic_only=payload.deterministic_only,
        save_results=True,
    )

    try:
        report = await service.analyze_strategy(req)
        return report
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        logger.error("Strategic analysis failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Strategic synthesis failed: {e}",
        ) from e


def _resolve_latest_strat_dir(crawl_run_id: str) -> Path:
    validate_id_str(crawl_run_id, "crawl_run_id")
    strat_base = Path("runs") / crawl_run_id / "analysis" / "strategic-intelligence"
    if not strat_base.exists() or not strat_base.is_dir():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No strategic runs for '{crawl_run_id}'.")

    subdirs = [d for d in strat_base.iterdir() if d.is_dir()]
    if not subdirs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No run records found.")

    return sorted(subdirs, key=lambda d: d.stat().st_mtime, reverse=True)[0]


@router.get("/{crawl_run_id}", response_model=dict[str, Any])
async def get_latest_strategic_report(crawl_run_id: str) -> dict[str, Any]:
    """Retrieve the latest complete strategic intelligence report."""
    run_dir = _resolve_latest_strat_dir(crawl_run_id)
    analysis_file = run_dir / "analysis.json"
    if not analysis_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="analysis.json missing.")
    return json.loads(analysis_file.read_text(encoding="utf-8"))


@router.get("/{crawl_run_id}/actions", response_model=list[dict[str, Any]])
async def get_roadmap_actions(crawl_run_id: str) -> list[dict[str, Any]]:
    """Retrieve the action backlog items."""
    run_dir = _resolve_latest_strat_dir(crawl_run_id)
    backlog_file = run_dir / "action-backlog.json"
    if not backlog_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="action-backlog.json missing.")
    return json.loads(backlog_file.read_text(encoding="utf-8"))


@router.get("/{crawl_run_id}/conflicts", response_model=list[dict[str, Any]])
async def get_conflicts(crawl_run_id: str) -> list[dict[str, Any]]:
    """Retrieve detected tradeoffs and conflicts."""
    run_dir = _resolve_latest_strat_dir(crawl_run_id)
    conf_file = run_dir / "conflicts.json"
    if not conf_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="conflicts.json missing.")
    return json.loads(conf_file.read_text(encoding="utf-8"))


@router.get("/{crawl_run_id}/roadmap", response_model=list[dict[str, Any]])
async def get_roadmap_waves(crawl_run_id: str) -> list[dict[str, Any]]:
    """Retrieve sequenced roadmap waves."""
    run_dir = _resolve_latest_strat_dir(crawl_run_id)
    roadmap_file = run_dir / "roadmap.json"
    if not roadmap_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="roadmap.json missing.")
    return json.loads(roadmap_file.read_text(encoding="utf-8"))


@router.patch("/{crawl_run_id}/actions/{action_id}", response_model=dict[str, Any])
async def update_action_status(
    crawl_run_id: str,
    action_id: str,
    payload: UpdateActionStatusPayload,
) -> dict[str, Any]:
    """Persistently update a roadmap action status with audit note."""
    validate_id_str(crawl_run_id, "crawl_run_id")
    validate_id_str(action_id, "action_id")

    run_dir = _resolve_latest_strat_dir(crawl_run_id)
    backlog_file = run_dir / "action-backlog.json"
    analysis_file = run_dir / "analysis.json"
    roadmap_file = run_dir / "roadmap.json"

    if not backlog_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="action-backlog.json missing.")

    actions = json.loads(backlog_file.read_text(encoding="utf-8"))
    updated = False
    for a in actions:
        if a.get("action_id") == action_id:
            a["status"] = payload.status
            if payload.notes:
                a["reviewer_notes"] = payload.notes
            a["updated_at"] = datetime.now(timezone.utc).isoformat()
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action '{action_id}' not found.")

    backlog_file.write_text(json.dumps(actions, indent=2, ensure_ascii=False), encoding="utf-8")

    # Sync back to analysis.json if present
    if analysis_file.exists():
        adata = json.loads(analysis_file.read_text(encoding="utf-8"))
        adata["actions"] = actions
        analysis_file.write_text(json.dumps(adata, indent=2, ensure_ascii=False), encoding="utf-8")

    # Sync back to roadmap.json if present
    if roadmap_file.exists():
        try:
            rdata = json.loads(roadmap_file.read_text(encoding="utf-8"))
            for wave in rdata:
                for wa in wave.get("actions", []):
                    if wa.get("action_id") == action_id:
                        wa["status"] = payload.status
            roadmap_file.write_text(json.dumps(rdata, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    return {
        "status": "success",
        "action_id": action_id,
        "new_status": payload.status,
        "reviewer": payload.reviewer,
        "notes": payload.notes,
    }
