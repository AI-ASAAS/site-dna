"""Browser lifecycle manager providing isolated Playwright Chromium execution."""

import asyncio
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Playwright, async_playwright

from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.visual import ViewportProfile
from site_dna.visual.browser_security import BrowserSecurityPolicy

logger = get_logger("visual.browser_manager")

SAFE_CHROMIUM_ARGS = [
    "--disable-background-networking",
    "--disable-default-apps",
    "--disable-sync",
    "--disable-translate",
    "--metrics-recording-only",
    "--mute-audio",
    "--no-first-run",
    "--safebrowsing-disable-auto-update",
]


class BrowserManager:
    """Manages asynchronous Playwright Chromium browser and isolated contexts."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._contexts: list[BrowserContext] = []
        self._semaphore = asyncio.Semaphore(self.settings.visual_max_concurrency)

    @property
    def desktop_profile(self) -> ViewportProfile:
        return ViewportProfile(
            name="desktop",
            width=self.settings.visual_desktop_width,
            height=self.settings.visual_desktop_height,
            device_scale_factor=1.0,
            is_mobile=False,
            has_touch=False,
        )

    @property
    def mobile_profile(self) -> ViewportProfile:
        return ViewportProfile(
            name="mobile",
            width=self.settings.visual_mobile_width,
            height=self.settings.visual_mobile_height,
            device_scale_factor=self.settings.visual_mobile_dpr,
            is_mobile=True,
            has_touch=True,
        )

    async def __aenter__(self) -> "BrowserManager":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self) -> None:
        """Launch Playwright Chromium instance in headless mode."""
        if self._browser is not None:
            return

        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.settings.visual_headless,
                args=SAFE_CHROMIUM_ARGS,
            )
            logger.info("Launched Chromium browser instance (v%s)", self._browser.version)
        except Exception as exc:
            logger.error("Failed to launch Playwright Chromium: %s", exc)
            await self.close()
            raise

    async def create_context(
        self,
        profile_name: str = "desktop",
        security_policy: Optional[BrowserSecurityPolicy] = None,
    ) -> BrowserContext:
        """Create a fresh, isolated browser context with profile emulation and network security."""
        if self._browser is None:
            await self.start()
        assert self._browser is not None

        profile = self.mobile_profile if profile_name == "mobile" else self.desktop_profile

        user_agent = (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
            if profile.is_mobile
            else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 SiteDNABot/0.1"
        )

        service_workers = "block" if self.settings.visual_block_service_workers else "allow"

        context = await self._browser.new_context(
            viewport={"width": profile.width, "height": profile.height},
            device_scale_factor=profile.device_scale_factor,
            is_mobile=profile.is_mobile,
            has_touch=profile.has_touch,
            user_agent=user_agent,
            locale="en-US",
            color_scheme="light",
            reduced_motion="reduce",
            permissions=[],
            service_workers=service_workers,
            ignore_https_errors=False,
        )

        # Attach network egress security policy
        if security_policy:
            await context.route("**/*", security_policy.handle_route)

        self._contexts.append(context)
        return context

    async def close_context(self, context: BrowserContext) -> None:
        """Safely close and clean up an individual browser context."""
        try:
            await context.close()
        except Exception as exc:
            logger.debug("Error closing context: %s", exc)
        finally:
            if context in self._contexts:
                self._contexts.remove(context)

    async def close(self) -> None:
        """Close all contexts and terminate the browser process."""
        for ctx in list(self._contexts):
            await self.close_context(ctx)
        self._contexts.clear()

        if self._browser:
            try:
                await self._browser.close()
            except Exception as exc:
                logger.debug("Error closing browser: %s", exc)
            self._browser = None

        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception as exc:
                logger.debug("Error stopping Playwright: %s", exc)
            self._playwright = None

        logger.info("BrowserManager shutdown complete.")
