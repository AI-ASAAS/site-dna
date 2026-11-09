"""Screenshot capture subsystem producing real PNG viewport and full-page captures."""

import hashlib
from pathlib import Path
from typing import Optional

from PIL import Image
from playwright.async_api import Page

from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.visual import ScreenshotRecord

logger = get_logger("visual.screenshots")


class ScreenshotCapture:
    """Takes stable viewport and full-page screenshots with dimensions and checksums."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    async def capture_screenshots(
        self,
        page: Page,
        output_dir: Path,
        profile_name: str,
    ) -> list[ScreenshotRecord]:
        """Capture both viewport and full-page screenshots for the active page."""
        output_dir.mkdir(parents=True, exist_ok=True)
        records: list[ScreenshotRecord] = []

        # 1. Viewport Screenshot
        vp_filename = f"{profile_name}-viewport.png"
        vp_path = output_dir / vp_filename
        try:
            await page.screenshot(
                path=str(vp_path),
                full_page=False,
                animations="disabled",
                caret="hide",
                scale="css",
            )
            records.append(self._build_record(vp_path, profile_name, "viewport"))
        except Exception as exc:
            logger.error("Viewport screenshot failed for %s: %s", page.url, exc)
            records.append(
                ScreenshotRecord(
                    viewport_profile=profile_name,
                    screenshot_type="viewport",
                    file_path=str(vp_path),
                    relative_path=vp_filename,
                    file_size_bytes=0,
                    width_px=0,
                    height_px=0,
                    sha256="",
                    success=False,
                    error=str(exc),
                )
            )

        # 2. Full-Page Screenshot (bounded by max_page_height)
        fp_filename = f"{profile_name}-full.png"
        fp_path = output_dir / fp_filename
        try:
            scroll_height = await page.evaluate(
                "() => document.documentElement.scrollHeight || document.body.scrollHeight"
            )
            max_height = self.settings.visual_max_page_height

            if scroll_height > max_height:
                logger.warning(
                    "Page scroll height (%d px) exceeds maximum ceiling (%d px). Full-page capture aborted for safety.",
                    scroll_height,
                    max_height,
                )
                records.append(
                    ScreenshotRecord(
                        viewport_profile=profile_name,
                        screenshot_type="full_page",
                        file_path=str(fp_path),
                        relative_path=fp_filename,
                        file_size_bytes=0,
                        width_px=0,
                        height_px=0,
                        sha256="",
                        success=False,
                        error=f"Scroll height ({scroll_height}px) exceeds safe ceiling ({max_height}px)",
                    )
                )
            else:
                await page.screenshot(
                    path=str(fp_path),
                    full_page=True,
                    animations="disabled",
                    caret="hide",
                    scale="css",
                )
                records.append(self._build_record(fp_path, profile_name, "full_page"))

        except Exception as exc:
            logger.error("Full-page screenshot failed for %s: %s", page.url, exc)
            records.append(
                ScreenshotRecord(
                    viewport_profile=profile_name,
                    screenshot_type="full_page",
                    file_path=str(fp_path),
                    relative_path=fp_filename,
                    file_size_bytes=0,
                    width_px=0,
                    height_px=0,
                    sha256="",
                    success=False,
                    error=str(exc),
                )
            )

        return records

    @staticmethod
    def _build_record(
        file_path: Path,
        profile_name: str,
        screenshot_type: str,
    ) -> ScreenshotRecord:
        """Read image file, compute SHA-256 hash and real pixel dimensions."""
        data = file_path.read_bytes()
        sha256 = hashlib.sha256(data).hexdigest()
        file_size = len(data)

        with Image.open(file_path) as img:
            width_px, height_px = img.size

        return ScreenshotRecord(
            viewport_profile=profile_name,
            screenshot_type=screenshot_type,  # type: ignore
            file_path=str(file_path),
            relative_path=file_path.name,
            file_size_bytes=file_size,
            width_px=width_px,
            height_px=height_px,
            sha256=sha256,
            success=True,
        )
