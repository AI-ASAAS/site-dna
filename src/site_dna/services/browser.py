"""Shared Playwright browser manager and SSRF-safe request guard (Phase 4)."""

from typing import Awaitable, Callable, Iterable, Optional
from urllib.parse import urlsplit

from playwright.async_api import Page, Route

from site_dna.core.logging import get_logger
from site_dna.services.security import DEFAULT_ALLOWED_PORTS, UrlRejected, validate_url
from site_dna.visual.browser_manager import BrowserManager as _PlaywrightBrowserManager

logger = get_logger("services.browser")

PASSTHROUGH_SCHEMES = frozenset({"data", "blob", "about"})
ALLOWED_REQUEST_SCHEMES = frozenset({"http", "https"})
BLOCKED_RESOURCE_TYPES = frozenset({"websocket", "eventsource"})
MAX_WARNINGS = 20

AsyncResolver = Callable[[str], Awaitable[list[str]]]


class BrowserRequestGuard:
    """Validate every browser request with the same policy as `validate_url`."""

    def __init__(
        self,
        *,
        allow_private_hosts: bool = False,
        allowed_ports: Optional[Iterable[int]] = None,
        resolver: Optional[AsyncResolver] = None,
    ) -> None:
        self._allow_private_hosts = allow_private_hosts
        self._allowed_ports = frozenset(allowed_ports) if allowed_ports is not None else DEFAULT_ALLOWED_PORTS
        self._resolver = resolver
        self._host_cache: dict[tuple[str, str, int], bool] = {}
        self.blocked_count = 0
        self.warnings: list[str] = []

    async def handle_route(self, route: Route) -> None:
        request = route.request
        url = request.url

        if request.resource_type in BLOCKED_RESOURCE_TYPES:
            await self._block(route, request.resource_type, "blocked_resource_type")
            return

        try:
            parts = urlsplit(url)
        except ValueError:
            await self._block(route, "invalid-url", "invalid_url")
            return

        scheme = parts.scheme.lower()
        if scheme in PASSTHROUGH_SCHEMES:
            await route.continue_()
            return
        if scheme not in ALLOWED_REQUEST_SCHEMES:
            await self._block(route, scheme or "unknown", "invalid_scheme")
            return

        host = (parts.hostname or "").lower()
        if parts.username or parts.password:
            await self._block(route, host or "unknown", "credentials_not_allowed")
            return
        if not host:
            await self._block(route, "unknown", "invalid_url")
            return

        try:
            port = parts.port or (80 if scheme == "http" else 443)
        except ValueError:
            await self._block(route, host, "port_not_allowed")
            return

        cache_key = (scheme, host, port)
        cached = self._host_cache.get(cache_key)
        if cached is False:
            await self._block(route, host, "cached_rejection")
            return
        if cached is True:
            await route.continue_()
            return

        try:
            await validate_url(
                url,
                allow_private_hosts=self._allow_private_hosts,
                allowed_ports=self._allowed_ports,
                resolver=self._resolver,
            )
        except UrlRejected as exc:
            self._host_cache[cache_key] = False
            await self._block(route, host, exc.code)
            return

        self._host_cache[cache_key] = True
        await route.continue_()

    async def _block(self, route: Route, target: str, code: str) -> None:
        self.blocked_count += 1
        if len(self.warnings) < MAX_WARNINGS:
            self.warnings.append(f"blocked browser request to {target} ({code})")
        logger.warning("Blocked browser request to %s (%s)", target, code)
        await route.abort("blockedbyclient")


class BrowserManager(_PlaywrightBrowserManager):
    """Playwright lifecycle manager shared by visual extraction and screenshots."""

    async def open_page(
        self,
        guard: Optional[BrowserRequestGuard] = None,
        *,
        profile: str = "desktop",
    ) -> Page:
        context = await self.create_context(profile, guard)  # type: ignore[arg-type]
        page = await context.new_page()
        page.set_default_timeout(self.settings.visual_navigation_timeout_ms)
        return page
