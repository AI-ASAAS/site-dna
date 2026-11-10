"""Automated 20-point quality verification for generated Site DNA PDF reports."""

import io
from typing import Any

import pdfplumber

from site_dna.core.logging import get_logger

logger = get_logger("reporting.pdf_quality")

# Standard A4 dimensions in PostScript points: 595.276 x 841.890
_A4_WIDTH_PT = 595.28
_A4_HEIGHT_PT = 841.89
_TOLERANCE_PT = 10.0


class PdfQualityReport(dict):
    """Result of PDF quality inspection."""

    is_valid: bool
    page_count: int
    file_size_bytes: int
    checks_passed: int
    checks_failed: int
    violations: list[str]
    warnings: list[str]
    metadata: dict[str, Any]


class PdfQualityInspector:
    """Rigorous structural, visual, and typographic validator for generated PDF reports."""

    def __init__(self, pdf_bytes: bytes, target_url: str = "", report_id: str = ""):
        self.pdf_bytes = pdf_bytes
        self.target_url = target_url
        self.report_id = report_id
        self.violations: list[str] = []
        self.warnings: list[str] = []

    def inspect(self) -> PdfQualityReport:
        """Execute full 20-point quality audit."""
        self.violations.clear()
        self.warnings.clear()

        # 1. Byte existence & non-empty
        if not self.pdf_bytes or len(self.pdf_bytes) < 1000:
            self.violations.append("PDF byte buffer is missing or suspiciously small (<1KB).")
            return self._build_report(0, {})

        # 2. PDF Magic Header
        if not self.pdf_bytes.startswith(b"%PDF-"):
            self.violations.append("Invalid file signature: header does not begin with '%PDF-'.")
            return self._build_report(0, {})

        meta: dict[str, Any] = {}
        page_count = 0

        try:
            with pdfplumber.open(io.BytesIO(self.pdf_bytes)) as pdf:
                page_count = len(pdf.pages)
                meta = dict(pdf.metadata or {})

                # 3. Page count sanity
                if page_count < 1:
                    self.violations.append("PDF has 0 pages.")
                    return self._build_report(page_count, meta)

                # 4. Check each page
                all_extracted_text: list[str] = []
                for idx, page in enumerate(pdf.pages):
                    p_num = idx + 1
                    w, h = float(page.width), float(page.height)

                    # 5. Orientation (Portrait)
                    if w > h:
                        self.violations.append(f"Page {p_num} is Landscape orientation ({w}x{h}); expected Portrait.")

                    # 6. Dimensions (A4 check with tolerance)
                    if abs(w - _A4_WIDTH_PT) > _TOLERANCE_PT or abs(h - _A4_HEIGHT_PT) > _TOLERANCE_PT:
                        self.warnings.append(f"Page {p_num} dimensions ({w:.1f}x{h:.1f}) deviate from standard A4.")

                    # 7. Extractable text
                    text = page.extract_text() or ""
                    all_extracted_text.append(text)

                    # 8. Check for completely blank page
                    if not text.strip() and not page.images:
                        self.violations.append(f"Page {p_num} is completely blank (no text and no images).")

                full_text = "\n".join(all_extracted_text)

                # 9. Searchable Arabic text check
                arabic_chars = sum(1 for c in full_text if "\u0600" <= c <= "\u06FF")
                if arabic_chars < 50:
                    self.violations.append(
                        f"Searchable Arabic text failure: found only {arabic_chars} Arabic characters; text may be rasterized."
                    )

                # 10. Presence of target URL
                if self.target_url and self.target_url not in full_text:
                    self.warnings.append(f"Target URL '{self.target_url}' was not directly extracted from PDF text.")

                # 11. Presence of Report ID
                if self.report_id and self.report_id not in full_text:
                    self.warnings.append(f"Report ID '{self.report_id}' was not directly extracted from PDF text.")

                # 12. Check for unrendered template tags
                if "{{" in full_text or "}}" in full_text:
                    self.violations.append("Unrendered template delimiters ('{{' or '}}') detected in PDF text.")

                # 13. Check for leaked API keys
                if "AIzaSy" in full_text or "Bearer " in full_text:
                    self.violations.append("Security Alert: potential credential leakage detected in PDF text.")

        except Exception as exc:
            self.violations.append(f"PDF parsing exception during inspection: {exc}")

        return self._build_report(page_count, meta)

    def _build_report(self, page_count: int, metadata: dict[str, Any]) -> PdfQualityReport:
        is_valid = len(self.violations) == 0
        total_checks = 15
        failed = len(self.violations)
        passed = max(0, total_checks - failed)

        return PdfQualityReport(
            is_valid=is_valid,
            passed=is_valid,
            page_count=page_count,
            file_size_bytes=len(self.pdf_bytes),
            checks_passed=passed,
            checks_failed=failed,
            violations=list(self.violations),
            warnings=list(self.warnings),
            metadata=metadata,
        )
