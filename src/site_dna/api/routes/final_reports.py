"""FastAPI endpoints for Site DNA Phase 12 — Final Reports & Enterprise PDF Export."""

from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from fastapi.responses import FileResponse, HTMLResponse

from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.reporting.export_service import FinalReportingService
from site_dna.schemas.final_report import (
    FinalReportMetadata,
    FinalReportRequest,
)

logger = get_logger("api.routes.final_reports")
router = APIRouter(prefix="/api/v1/reports/final", tags=["Final Reports & PDF Export"])


def get_reporting_service(settings: Settings = Depends(get_settings)) -> FinalReportingService:
    return FinalReportingService(settings=settings)


def verify_report_auth(
    authorization: Optional[str] = Header(None),
    settings: Settings = Depends(get_settings),
) -> None:
    token = getattr(settings, "report_export_token", None) or getattr(settings, "strategic_analysis_token", None)
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
            detail="Invalid report authorization token.",
        )


@router.post(
    "",
    response_model=FinalReportMetadata,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_report_auth)],
    summary="Generate a new final report and PDF export",
)
async def generate_final_report(
    payload: FinalReportRequest,
    service: FinalReportingService = Depends(get_reporting_service),
) -> FinalReportMetadata:
    """Generate comprehensive or executive report with PDF, Markdown, and JSON artifacts."""
    return await service.generate_final_report(payload)


@router.get(
    "/{crawl_run_id}",
    response_model=list[FinalReportMetadata],
    summary="List all generated report versions for a run",
)
def list_final_reports(
    crawl_run_id: str,
    service: FinalReportingService = Depends(get_reporting_service),
) -> list[FinalReportMetadata]:
    """Retrieve all previously generated report versions for an analysis run."""
    return service.list_reports(crawl_run_id)


@router.get(
    "/{crawl_run_id}/{report_id}",
    response_model=FinalReportMetadata,
    summary="Retrieve report metadata by ID",
)
def get_report_metadata(
    crawl_run_id: str,
    report_id: str,
    service: FinalReportingService = Depends(get_reporting_service),
) -> FinalReportMetadata:
    """Get metadata for a specific report ID."""
    return service.get_report_metadata(crawl_run_id, report_id)


@router.get(
    "/{crawl_run_id}/{report_id}/download",
    summary="Download report file (PDF, Markdown, HTML, JSON)",
)
def download_report_file(
    crawl_run_id: str,
    report_id: str,
    format: str = Query("pdf", description="Format: pdf, html, markdown, json"),
    service: FinalReportingService = Depends(get_reporting_service),
) -> FileResponse:
    """Download the requested report artifact with safe Content-Disposition headers."""
    target_file, mime_type = service.get_report_artifact_file(crawl_run_id, report_id, file_type=format)
    ext = "md" if format in ("md", "markdown") else format
    download_filename = f"site-dna-report-{report_id}.{ext}"

    return FileResponse(
        path=target_file,
        media_type=mime_type,
        filename=download_filename,
        headers={
            "Cache-Control": "private, max-age=3600",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get(
    "/{crawl_run_id}/{report_id}/preview",
    response_class=HTMLResponse,
    summary="Preview report HTML directly in browser or iframe",
)
def preview_report_html(
    crawl_run_id: str,
    report_id: str,
    service: FinalReportingService = Depends(get_reporting_service),
) -> HTMLResponse:
    """Serve report HTML for responsive browser preview."""
    target_file, _ = service.get_report_artifact_file(crawl_run_id, report_id, file_type="html")
    html_content = target_file.read_text(encoding="utf-8")
    return HTMLResponse(content=html_content)


@router.get(
    "/{crawl_run_id}/{report_id}/artifacts",
    summary="Inspect generated report artifacts with file status",
)
def list_report_artifacts(
    crawl_run_id: str,
    report_id: str,
    service: FinalReportingService = Depends(get_reporting_service),
) -> dict[str, Any]:
    """Retrieve list of generated artifacts for a report with existence and paths."""
    meta = service.get_report_metadata(crawl_run_id, report_id)
    rep_dir = Path("runs") / crawl_run_id / "reports" / "final" / report_id
    artifacts_map = {}
    for fn, ftype in [
        ("report.pdf", "pdf"),
        ("report.html", "html"),
        ("report.md", "markdown"),
        ("report-data.json", "json"),
        ("source-manifest.json", "manifest"),
        ("pdf-validation.json", "validation"),
    ]:
        p = rep_dir / fn
        artifacts_map[ftype] = {
            "filename": fn,
            "exists": p.exists(),
            "size_bytes": p.stat().st_size if p.exists() else 0,
            "path": str(p),
        }
    return {"crawl_run_id": crawl_run_id, "report_id": report_id, "artifacts": artifacts_map}

