"""High-level export and reporting service managing report generation and persistence."""

from pathlib import Path
import re
from typing import Optional

from fastapi import HTTPException, status

from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.flows.final_report_flow import FinalReportFlow
from site_dna.schemas.final_report import (
    FinalReportMetadata,
    FinalReportRequest,
)

logger = get_logger("reporting.service")
_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]+$")


def validate_id(val: str, name: str = "ID") -> None:
    if not val or not _ID_REGEX.match(val):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {name} format: '{val}'. Only alphanumeric characters and hyphens allowed.",
        )


class FinalReportingService:
    """Service orchestrating final report generation, artifact persistence, and download retrieval."""

    def __init__(self, settings: Optional[Settings] = None, base_runs_dir: Optional[Path] = None):
        self.settings = settings or get_settings()
        self.base_runs_dir = base_runs_dir or Path("runs")

    async def generate_final_report(self, request: FinalReportRequest) -> FinalReportMetadata:
        """Execute FinalReportFlow and return generated report metadata."""
        validate_id(request.crawl_run_id, "crawl_run_id")

        flow = FinalReportFlow(request=request, settings=self.settings, base_runs_dir=self.base_runs_dir)
        try:
            # Execute flow steps
            flow.validate_request()
            ctx = flow.assemble_context({})
            flow.validate_evidence_integrity(ctx)
            html = flow.render_html_and_markdown(ctx)
            pdf = await flow.render_pdf_document(html)
            qual = flow.inspect_pdf_quality(pdf)
            meta = flow.persist_artifacts(qual)
            return meta
        except HTTPException:
            raise
        except FileNotFoundError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
        except Exception as e:
            logger.error("Final report generation failed: %s", e, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Final report generation failed: {e}",
            ) from e

    # Alias for convenience across coordinator and CLI
    generate_report = generate_final_report

    def list_reports(self, crawl_run_id: str) -> list[FinalReportMetadata]:
        """List all generated final report versions for a run."""
        validate_id(crawl_run_id, "crawl_run_id")
        rep_base = self.base_runs_dir / crawl_run_id / "reports" / "final"
        if not rep_base.exists() or not rep_base.is_dir():
            return []

        results: list[FinalReportMetadata] = []
        for rdir in rep_base.iterdir():
            if not rdir.is_dir():
                continue
            sum_file = rdir / "export-summary.json"
            if sum_file.exists():
                try:
                    meta = FinalReportMetadata.model_validate_json(sum_file.read_text(encoding="utf-8"))
                    results.append(meta)
                except Exception:
                    pass

        # Sort newest first
        return sorted(results, key=lambda m: m.created_at, reverse=True)

    def get_report_metadata(self, crawl_run_id: str, report_id: str) -> FinalReportMetadata:
        """Retrieve metadata for a specific report."""
        validate_id(crawl_run_id, "crawl_run_id")
        validate_id(report_id, "report_id")

        sum_file = self.base_runs_dir / crawl_run_id / "reports" / "final" / report_id / "export-summary.json"
        if not sum_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report '{report_id}' not found for run '{crawl_run_id}'.",
            )

        return FinalReportMetadata.model_validate_json(sum_file.read_text(encoding="utf-8"))

    def get_report_artifact_file(self, crawl_run_id: str, report_id: str, file_type: str = "pdf") -> tuple[Path, str]:
        """Resolve artifact file path and MIME type."""
        validate_id(crawl_run_id, "crawl_run_id")
        validate_id(report_id, "report_id")

        rep_dir = self.base_runs_dir / crawl_run_id / "reports" / "final" / report_id
        if not rep_dir.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report '{report_id}' not found.")

        mime_types = {
            "pdf": ("report.pdf", "application/pdf"),
            "html": ("report.html", "text/html; charset=utf-8"),
            "md": ("report.md", "text/markdown; charset=utf-8"),
            "markdown": ("report.md", "text/markdown; charset=utf-8"),
            "json": ("report-data.json", "application/json"),
        }

        if file_type not in mime_types:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported format '{file_type}'.")

        fname, mime = mime_types[file_type]
        target_file = rep_dir / fname
        if not target_file.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Artifact '{fname}' not found.")

        return target_file, mime


FinalReportExportService = FinalReportingService

