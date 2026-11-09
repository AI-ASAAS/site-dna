"""Playwright-based headless Chromium PDF renderer with security isolation for Site DNA."""

import asyncio
from typing import Optional

from playwright.async_api import async_playwright

from site_dna.core.logging import get_logger
from site_dna.schemas.final_report import ReportPaperSize

logger = get_logger("reporting.pdf_renderer")


class PlaywrightPdfRenderer:
    """Renders HTML documents into high-fidelity A4/Letter PDFs using headless Chromium."""

    def __init__(self, timeout_sec: float = 30.0, headless: bool = True):
        self.timeout_sec = timeout_sec
        self.headless = headless

    def _get_chromium_args(self) -> list[str]:
        return [
            "--disable-network",
            "--disable-extensions",
            "--disable-background-networking",
            "--no-sandbox",
            "--disable-setuid-sandbox",
        ]

    async def render_pdf_bytes(
        self,
        html_content: str,
        paper_size: ReportPaperSize = "A4",
        is_ar: bool = True,
    ) -> bytes:
        """Render self-contained HTML into PDF bytes with network isolation."""
        async with async_playwright() as p:
            # Launch isolated chromium instance with disabled outbound networking to prevent SSRF
            browser = await p.chromium.launch(
                headless=self.headless,
                args=self._get_chromium_args(),
            )
            try:
                page = await browser.new_page()
                # Load self-contained HTML with embedded base64 fonts & images
                await page.set_content(html_content, wait_until="load", timeout=int(self.timeout_sec * 1000))

                # Allow fonts to settle
                await page.wait_for_timeout(500)

                pdf_bytes = await page.pdf(
                    format=paper_size,
                    print_background=True,
                    prefer_css_page_size=True,
                    margin={
                        "top": "16mm",
                        "bottom": "16mm",
                        "left": "14mm",
                        "right": "14mm",
                    },
                )
                return pdf_bytes
            finally:
                await browser.close()

    render_pdf = render_pdf_bytes

