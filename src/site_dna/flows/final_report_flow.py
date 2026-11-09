"""CrewAI Flow orchestrating Phase 12 Final Reporting, Synthesis & PDF Generation."""

import json
from pathlib import Path
from typing import Any, Optional

from crewai.flow.flow import Flow, listen, start

from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.reporting.pdf_quality import PdfQualityInspector
from site_dna.reporting.pdf_renderer import PlaywrightPdfRenderer
from site_dna.reporting.report_context import ReportContextBuilder
from site_dna.reporting.report_validator import ReportIntegrityValidator
from site_dna.reporting.source_adapters import compute_sha256
from site_dna.reporting.templates import render_html_report
from site_dna.schemas.final_report import (
    FinalReportContext,
    FinalReportMetadata,
    FinalReportRequest,
)

logger = get_logger("flows.final_report")


class FinalReportFlow(Flow):
    """CrewAI Flow for assembling canonical report contexts and generating verified enterprise PDFs."""

    def __init__(
        self,
        request: FinalReportRequest,
        settings: Optional[Settings] = None,
        base_runs_dir: Optional[Path] = None,
    ):
        super().__init__()
        self.request = request
        self.settings = settings or get_settings()
        self.base_runs_dir = base_runs_dir or Path("runs")
        self.run_dir = self.base_runs_dir / request.crawl_run_id

        # Internal state
        self.context: Optional[FinalReportContext] = None
        self.html_content: str = ""
        self.pdf_bytes: bytes = b""
        self.validation_result: dict[str, Any] = {}
        self.metadata: Optional[FinalReportMetadata] = None

    @start()
    def validate_request(self) -> dict[str, Any]:
        """Validate source run directory and initialize workflow."""
        if not self.run_dir.exists() or not self.run_dir.is_dir():
            raise FileNotFoundError(f"Run directory '{self.run_dir}' does not exist.")

        logger.info("Starting FinalReportFlow for run %s (mode=%s)", self.request.crawl_run_id, self.request.mode)
        return {"status": "request_validated", "run_id": self.request.crawl_run_id}

    @listen(validate_request)
    def assemble_context(self, prev_state: dict[str, Any]) -> FinalReportContext:
        """Extract multi-phase evidence and build canonical report context."""
        builder = ReportContextBuilder(self.run_dir)
        self.context = builder.build_context(
            mode=self.request.mode,
            language=self.request.language,
            paper_size=self.request.paper_size,
            target_agent=self.request.target_agent,
        )
        return self.context

    @listen(assemble_context)
    def validate_evidence_integrity(self, ctx: FinalReportContext) -> FinalReportContext:
        """Run Zero-Hallucination evidence grounding validator."""
        validator = ReportIntegrityValidator(ctx)
        is_valid, violations, warnings = validator.validate()

        if not is_valid:
            logger.warning("Report validation detected %d violations: %s", len(violations), violations)
            # Annotate context
            ctx.status = "validation_failed"
            ctx.limitations.extend([f"ملاحظة تدقيق: {v}" for v in violations])

        return ctx

    @listen(validate_evidence_integrity)
    def render_html_and_markdown(self, ctx: FinalReportContext) -> str:
        """Render complete HTML and Markdown representations."""
        self.html_content = render_html_report(ctx)
        return self.html_content

    @listen(render_html_and_markdown)
    async def render_pdf_document(self, html: str) -> bytes:
        """Render PDF via headless Playwright Chromium."""
        renderer = PlaywrightPdfRenderer(timeout_sec=40.0)
        self.pdf_bytes = await renderer.render_pdf_bytes(
            html_content=html,
            paper_size=self.request.paper_size,
            is_ar=(self.request.language == "ar"),
        )
        return self.pdf_bytes

    @listen(render_pdf_document)
    def inspect_pdf_quality(self, pdf: bytes) -> dict[str, Any]:
        """Audit the generated PDF for layout, typography, and text extraction."""
        inspector = PdfQualityInspector(
            pdf_bytes=pdf,
            target_url=self.context.target_url if self.context else "",
            report_id=self.context.report_id if self.context else "",
        )
        report = inspector.inspect()
        self.validation_result = report
        return report

    @listen(inspect_pdf_quality)
    def persist_artifacts(self, qual: dict[str, Any]) -> FinalReportMetadata:
        """Save all report artifacts in immutable versioned directories."""
        ctx = self.context
        assert ctx is not None

        rep_dir = self.run_dir / "reports" / "final" / ctx.report_id
        rep_dir.mkdir(parents=True, exist_ok=True)

        # 1. report.html
        html_file = rep_dir / "report.html"
        html_file.write_text(self.html_content, encoding="utf-8")

        # 2. report.pdf
        pdf_file = rep_dir / "report.pdf"
        pdf_file.write_bytes(self.pdf_bytes)

        # 3. report-data.json
        data_file = rep_dir / "report-data.json"
        data_file.write_text(ctx.model_dump_json(indent=2), encoding="utf-8")

        # 4. report.md
        md_file = rep_dir / "report.md"
        md_content = f"# {ctx.target_url} — Audit Report\n\n{ctx.executive_summary_md}\n\n## Findings\n\n"
        for f in ctx.findings:
            md_content += f"- **[{f.severity.upper()}]** {f.title}: {f.description}\n"
        md_file.write_text(md_content, encoding="utf-8")

        # 5. source-manifest.json
        manifest_file = rep_dir / "source-manifest.json"
        manifest_data = [p.model_dump() for p in ctx.source_manifest]
        manifest_file.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")

        # 6. evidence-index.json
        ev_file = rep_dir / "evidence-index.json"
        ev_data = [e.model_dump() for e in ctx.evidence_catalog]
        ev_file.write_text(json.dumps(ev_data, indent=2, ensure_ascii=False), encoding="utf-8")

        # 7. pdf-validation.json
        val_file = rep_dir / "pdf-validation.json"
        val_file.write_text(json.dumps(self.validation_result, indent=2, ensure_ascii=False), encoding="utf-8")

        # Compute PDF checksum
        pdf_sha = compute_sha256(pdf_file)

        # 8. export-summary.json
        meta = FinalReportMetadata(
            report_id=ctx.report_id,
            report_version=ctx.report_version,
            target_url=ctx.target_url,
            crawl_run_id=ctx.crawl_run_id,
            mode=ctx.mode,
            language=ctx.language,
            paper_size=ctx.paper_size,
            status=ctx.status,
            overall_score=ctx.strategic_index,
            page_count=qual.get("page_count", 1),
            pdf_size_bytes=len(self.pdf_bytes),
            sha256_checksum=pdf_sha,
            available_agents_count=len(ctx.coverage.get("available_stages", [])),
            total_findings_count=len(ctx.findings),
            critical_findings_count=len(ctx.critical_issues),
            total_actions_count=len(ctx.recommendations),
            pdf_path=str(pdf_file),
            html_path=str(html_file),
            markdown_path=str(md_file),
            json_path=str(data_file),
        )

        sum_file = rep_dir / "export-summary.json"
        sum_file.write_text(meta.model_dump_json(indent=2), encoding="utf-8")

        self.metadata = meta
        logger.info("Final report %s generated successfully (%d pages, %d bytes)", ctx.report_id, meta.page_count, meta.pdf_size_bytes)
        return meta
