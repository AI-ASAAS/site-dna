"""FastAPI route for protected visual evidence collection and browser rendering."""

import re
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.discovery import CrawlResult
from site_dna.schemas.visual import VisualCaptureRequest, VisualCaptureResult
from site_dna.visual.service import VisualCollectionService

logger = get_logger("api.routes.visual")

router = APIRouter(prefix="/api/v1/visual", tags=["Visual"])


def verify_visual_access(
    request: Request,
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    """Validate that visual capture API is enabled, local, and authenticated."""
    # Gate 1: Enabled flag
    if not settings.visual_api_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Visual capture API is disabled. Set VISUAL_API_ENABLED=true in configuration.",
        )

    # Gate 2: Localhost check in development
    if settings.app_env == "development":
        client_host = request.client.host if request.client else ""
        if client_host not in ("127.0.0.1", "::1", "localhost", "testclient"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Visual capture API only accepts loopback requests in development mode, got {client_host}.",
            )

    # Gate 3: Bearer token verification if configured
    if settings.visual_api_token and settings.visual_api_token.get_secret_value().strip():
        expected_token = settings.visual_api_token.get_secret_value().strip()
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
                detail="Invalid visual API authorization token.",
                headers={"WWW-Authenticate": "Bearer"},
            )


@router.post(
    "/capture",
    response_model=VisualCaptureResult,
    status_code=status.HTTP_200_OK,
    summary="Trigger visual evidence collection for a crawled website run",
    dependencies=[Depends(verify_visual_access)],
)
async def capture_visual_evidence(
    request_data: VisualCaptureRequest,
    settings: Settings = Depends(get_settings),
) -> VisualCaptureResult:
    """Execute browser rendering and screenshot collection on previously discovered pages."""
    logger.info("Received visual capture request for crawl_run_id=%s", request_data.crawl_run_id)

    # Validate and resolve crawl artifact path (preventing path traversal)
    crawl_file_path: Path
    if request_data.crawl_file:
        raw_path = Path(request_data.crawl_file)
        if ".." in raw_path.parts:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path traversal not permitted.")
        crawl_file_path = raw_path
    elif request_data.crawl_run_id:
        clean_id = re.sub(r"[^a-zA-Z0-9_-]", "", request_data.crawl_run_id)
        crawl_file_path = Path("runs") / clean_id / "crawl.json"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify either crawl_run_id or crawl_file.",
        )

    if not crawl_file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crawl artifact file not found at {crawl_file_path}",
        )

    try:
        crawl_json = crawl_file_path.read_text(encoding="utf-8")
        crawl_result = CrawlResult.model_validate_json(crawl_json)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse crawl result JSON: {exc}",
        ) from exc

    service = VisualCollectionService(settings=settings)
    result = await service.collect_visual_evidence(
        crawl_result=crawl_result,
        max_pages=request_data.max_pages,
    )
    return result
