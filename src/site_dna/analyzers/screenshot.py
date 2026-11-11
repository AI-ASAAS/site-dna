"""Screenshot capture engine for the Website Intelligence MVP (Phase 5)."""

import asyncio
import base64
import hashlib
import time
from pathlib import Path
from typing import Any

from playwright.async_api import Page

from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.models.common import FileRef, ModuleError, ModuleResult, ModuleStatus
from site_dna.models.visual import ScreenshotResult, ScreenshotViewport
from site_dna.services.browser import BrowserManager, BrowserRequestGuard

logger = get_logger("analyzers.screenshot")

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
NETWORK_IDLE_TIMEOUT_MS = 3000
IMAGE_WAIT_TIMEOUT_MS = 3000
SCROLL_PAUSE_MS = 120
SETTLE_DELAY_MS = 250
MAX_SCROLL_STEPS = 40

PAGE_HEIGHT_JS = """() => Math.max(
  document.documentElement ? document.documentElement.scrollHeight : 0,
  document.body ? document.body.scrollHeight : 0
)"""

FORCE_EAGER_JS = """() => {
  let changed = 0;
  for (const image of document.images) {
    if (image.loading === "lazy") {
      image.loading = "eager";
      changed += 1;
    }
  }
  return changed;
}"""

IMAGES_COMPLETE_JS = """() => Array.from(document.images).every((image) => image.complete)"""


def read_png_dimensions(data: bytes) -> tuple[int, int]:
    """Read width and height from the PNG IHDR chunk without decoding the image."""
    if len(data) < 24 or data[:8] != PNG_SIGNATURE or data[12:16] != b"IHDR":
        raise ValueError("not a PNG image with an IHDR chunk")
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    if width <= 0 or height <= 0:
        raise ValueError("invalid PNG dimensions")
    return width, height


class ScreenshotEngine:
    """Capture a full-page PNG using the shared browser manager and request guard."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        guard: BrowserRequestGuard | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._guard = guard

    async def capture(
        self,
        url: str,
        scan_id: str,
        *,
        embed_images: bool = False,
    ) -> ModuleResult[ScreenshotResult]:
        """Capture `url` and return a file reference plus capture metadata."""
        started = time.perf_counter()
        guard = self._guard or BrowserRequestGuard(
            allow_private_hosts=self._settings.private_hosts_allowed()
        )

        try:
            _validate_scan_id(scan_id)
            async with BrowserManager(settings=self._settings) as manager:
                page = await manager.open_page(guard)
                try:
                    data = await self._capture_page(page, url, scan_id, embed_images)
                finally:
                    await manager.close_context(page.context)
        except Exception as exc:  # noqa: BLE001 - module boundary reports a failed result
            logger.warning("screenshot capture failed", extra={"url": url})
            return ModuleResult[ScreenshotResult](
                status=ModuleStatus.failed,
                reason=str(exc),
                duration_ms=_elapsed_ms(started),
                warnings=list(guard.warnings),
                errors=[
                    ModuleError(
                        code="screenshot_failed",
                        message=str(exc),
                        url=url,
                    )
                ],
            )

        warnings = list(guard.warnings)
        status = ModuleStatus.ok
        if guard.blocked_count:
            status = ModuleStatus.partial
            warnings.append(f"{guard.blocked_count} browser request(s) blocked")

        return ModuleResult[ScreenshotResult](
            status=status,
            duration_ms=_elapsed_ms(started),
            data=data,
            warnings=warnings,
        )

    async def _capture_page(
        self,
        page: Page,
        url: str,
        scan_id: str,
        embed_images: bool,
    ) -> ScreenshotResult:
        settings = self._settings
        viewport_width = settings.visual_desktop_width
        viewport_height = settings.visual_desktop_height
        max_height = settings.scan_screenshot_max_height

        await page.goto(
            url,
            wait_until="load",
            timeout=settings.visual_navigation_timeout_ms,
        )
        try:
            await page.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_TIMEOUT_MS)
        except Exception:  # noqa: BLE001 - bounded wait is allowed to fail
            pass

        await page.evaluate(FORCE_EAGER_JS)
        scrolled_steps = await self._scroll_through_page(page, viewport_height, max_height)
        await page.evaluate("window.scrollTo(0, 0)")

        try:
            await asyncio.wait_for(
                page.evaluate("document.fonts.ready"),
                timeout=settings.visual_font_wait_timeout_ms / 1000,
            )
        except Exception:  # noqa: BLE001 - font readiness is best effort
            pass
        try:
            await page.wait_for_function(IMAGES_COMPLETE_JS, timeout=IMAGE_WAIT_TIMEOUT_MS)
        except Exception:  # noqa: BLE001 - broken images must not fail the capture
            pass
        await page.wait_for_timeout(SETTLE_DELAY_MS)

        document_height = await self._page_height(page)
        truncated = document_height > max_height
        capture_height = min(document_height, max_height)
        target = Path(settings.storage_dir) / scan_id / "homepage.png"
        target.parent.mkdir(parents=True, exist_ok=True)

        screenshot_options: dict[str, Any] = {
            "path": str(target),
            "full_page": True,
            "type": "png",
            "animations": "disabled",
            "caret": "hide",
        }
        if truncated:
            screenshot_options["clip"] = {
                "x": 0,
                "y": 0,
                "width": viewport_width,
                "height": capture_height,
            }

        await page.screenshot(**screenshot_options)
        raw = target.read_bytes()
        width, height = read_png_dimensions(raw)
        file_ref = FileRef(
            path=str(target),
            format="png",
            bytes=len(raw),
            sha256=hashlib.sha256(raw).hexdigest(),
            width=width,
            height=height,
        )

        return ScreenshotResult(
            file=file_ref,
            document_height=document_height,
            viewport=ScreenshotViewport(width=viewport_width, height=viewport_height),
            truncated=truncated,
            scrolled_steps=scrolled_steps,
            base64=base64.b64encode(raw).decode("ascii") if embed_images else None,
        )

    async def _scroll_through_page(self, page: Page, viewport_height: int, max_height: int) -> int:
        last_height = await self._page_height(page)
        steps = 0
        scroll_y = 0
        while steps < MAX_SCROLL_STEPS:
            steps += 1
            scroll_y += viewport_height
            await page.evaluate("(y) => window.scrollTo(0, y)", scroll_y)
            await page.wait_for_timeout(SCROLL_PAUSE_MS)
            height = await self._page_height(page)
            if scroll_y >= height and height <= last_height:
                break
            last_height = height
            if height >= max_height:
                break
        return steps

    async def _page_height(self, page: Page) -> int:
        value = await page.evaluate(PAGE_HEIGHT_JS)
        return int(value or 0)


def _validate_scan_id(scan_id: str) -> None:
    if not scan_id or scan_id in {".", ".."} or "/" in scan_id or "\\" in scan_id:
        raise ValueError("invalid scan_id")


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)
