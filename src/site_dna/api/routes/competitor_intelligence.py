"""FastAPI router for Site DNA Phase 08 — Competitor Intelligence."""

import json
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status

from site_dna.analysis.competitor_intelligence.service import CompetitorIntelligenceService
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.competitor_intelligence import (
    CompetitorAnalysisRequest,
    CompetitorIntelligenceReport,
    FeatureComparisonRecord,
)

logger = get_logger("api.routes.competitor_intelligence")

router = APIRouter(prefix="/api/v1/analysis", tags=["Competitor Intelligence"])


def get_competitor_service(settings: Settings = Depends(get_settings)) -> CompetitorIntelligenceService:
    """Dependency provider for CompetitorIntelligenceService."""
    return CompetitorIntelligenceService(base_dir="runs", settings=settings)


def verify_competitor_api_token(
    authorization: Optional[str] = Header(None),
    settings: Settings = Depends(get_settings),
) -> None:
    """Enforce optional Bearer token authentication if configured."""
    expected = settings.get_effective_competitor_token()
    if not expected:
        return

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Bearer authentication token.",
        )

    token = authorization.split("Bearer ", 1)[1].strip()
    if token != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authentication token for Competitor Intelligence API.",
        )


@router.post(
    "/competitors",
    response_model=CompetitorIntelligenceReport,
    status_code=status.HTTP_200_OK,
    summary="Execute multi-site competitor benchmarking audit",
    dependencies=[Depends(verify_competitor_api_token)],
)
async def analyze_competitors_endpoint(
    request: CompetitorAnalysisRequest,
    service: CompetitorIntelligenceService = Depends(get_competitor_service),
    settings: Settings = Depends(get_settings),
) -> CompetitorIntelligenceReport:
    """Analyze primary website against 1 to 5 competitors producing evidence-backed benchmarking."""
    if not settings.competitor_analysis_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Competitor Intelligence analysis is disabled by configuration.",
        )

    if not request.primary_run_id and not request.primary_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'primary_run_id' or 'primary_url' must be specified.",
        )

    total_comps = len(request.competitor_urls) + len(request.competitor_run_ids or [])
    if total_comps < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one competitor URL or run ID must be provided.",
        )

    if total_comps > settings.competitor_analysis_hard_max_competitors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Exceeded hard limit of {settings.competitor_analysis_hard_max_competitors} competitors.",
        )

    try:
        report = await service.analyze_competitors(request)
        return report
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(fnf)) from fnf
    except Exception as exc:
        logger.error("Competitor benchmark failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Competitor Intelligence audit failed: {exc}",
        ) from exc


@router.get(
    "/competitors/{comparison_run_id}",
    response_model=CompetitorIntelligenceReport,
    summary="Retrieve completed competitor benchmark report",
)
async def get_competitor_report(
    comparison_run_id: str,
    service: CompetitorIntelligenceService = Depends(get_competitor_service),
) -> CompetitorIntelligenceReport:
    """Fetch stored competitor intelligence benchmark by comparison_run_id."""
    clean_id = "".join(c for c in comparison_run_id if c.isalnum() or c in "-_")
    matches = list(service.base_dir.glob(f"*/analysis/competitors/{clean_id}/analysis.json"))
    if not matches:
        matches = list(service.base_dir.glob(f"{clean_id}/analysis/competitors/*/analysis.json"))
    if not matches:
        matches = list(service.base_dir.glob(f"**/{clean_id}/analysis.json"))
    if not matches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitor comparison run '{comparison_run_id}' not found.",
        )

    target_file = matches[-1]
    try:
        data = json.loads(target_file.read_text(encoding="utf-8"))
        return CompetitorIntelligenceReport.model_validate(data)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed loading competitor report: {exc}",
        ) from exc


@router.get(
    "/competitors/{comparison_run_id}/matrix",
    response_model=list[FeatureComparisonRecord],
    summary="Retrieve feature comparison matrix",
)
async def get_feature_matrix(
    comparison_run_id: str,
    service: CompetitorIntelligenceService = Depends(get_competitor_service),
) -> list[FeatureComparisonRecord]:
    """Retrieve normalized feature comparison matrix for a benchmark run."""
    clean_id = "".join(c for c in comparison_run_id if c.isalnum() or c in "-_")
    matches = list(service.base_dir.glob(f"*/analysis/competitors/{clean_id}/feature-matrix.json"))
    if not matches:
        matches = list(service.base_dir.glob(f"{clean_id}/analysis/competitors/*/feature-matrix.json"))
    if not matches:
        matches = list(service.base_dir.glob(f"**/{clean_id}/feature-matrix.json"))
    if not matches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature matrix for run '{comparison_run_id}' not found.",
        )

    try:
        data = json.loads(matches[-1].read_text(encoding="utf-8"))
        return [FeatureComparisonRecord.model_validate(item) for item in data]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed loading feature matrix: {exc}",
        ) from exc
