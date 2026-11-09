"""Page rendering engine handling navigation milestones, font readiness, and hydration."""

import asyncio
import time
from typing import Optional

from playwright.async_api import BrowserContext, Page

from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger

logger = get_logger("visual.renderer")


class RenderResult:
    """Outcome of rendering a web page in a browser context."""

    def __init__(
        self,
        page: Optional[Page],
        final_url: str,
        status_code: int = 200,
        success: bool = True,
        error: Optional[str] = None,
        duration_ms: float = 0.0,
    ):
        self.page = page
        self.final_url = final_url
        self.status_code = status_code
        self.success = success
        self.error = error
        self.duration_ms = duration_ms


class PageRenderer:
    """Renders web pages using bounded readiness strategies."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    async def render_page(
        self,
        url: str,
        context: BrowserContext,
    ) -> RenderResult:
        """Open and render a page within the given browser context."""
        start_time = time.perf_counter()
        page = await context.new_page()

        # Automatically dismiss alert/confirm/prompt dialogs
        page.on("dialog", lambda dialog: asyncio.create_task(dialog.dismiss()))

        try:
            timeout_ms = self.settings.visual_navigation_timeout_ms
            logger.debug("Navigating browser to: %s (timeout: %d ms)", url, timeout_ms)

            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=timeout_ms,
            )

            status_code = response.status if response else 200

            # Wait for document.body availability
            await page.wait_for_selector("body", timeout=5000, state="attached")

            # Bounded wait for fonts readiness
            font_timeout = self.settings.visual_font_wait_timeout_ms / 1000.0
            try:
                await asyncio.wait_for(
                    page.evaluate("document.fonts.ready"),
                    timeout=font_timeout,
                )
            except (asyncio.TimeoutError, Exception) as font_err:
                logger.debug("Font readiness wait expired or failed: %s", font_err)

            # Short layout stabilization pause
            await asyncio.sleep(0.1)

            final_url = page.url
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            return RenderResult(
                page=page,
                final_url=final_url,
                status_code=status_code,
                success=True,
                duration_ms=round(duration_ms, 2),
            )

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.warning("Render failed for %s: %s", url, exc)
            try:
                await page.close()
            except Exception:
                pass

            return RenderResult(
                page=None,
                final_url=url,
                status_code=500,
                success=False,
                error=f"{type(exc).__name__}: {str(exc)}",
                duration_ms=round(duration_ms, 2),
            )
