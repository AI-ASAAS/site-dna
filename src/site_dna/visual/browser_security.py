"""Browser network egress security, subresource filtering, and SSRF prevention for Playwright."""

from typing import Optional
from urllib.parse import urlsplit

from playwright.async_api import Route

from site_dna.core.logging import get_logger
from site_dna.core.security import FORBIDDEN_HOSTNAMES, resolve_and_validate_host

logger = get_logger("visual.browser_security")

ALLOWED_BROWSER_SCHEMES = frozenset({"http", "https", "data", "blob", "about"})
BLOCKED_RESOURCE_TYPES = frozenset({"websocket", "eventsource"})


class BrowserSecurityPolicy:
    """Manages browser-level request filtering, egress boundaries, and SSRF protection."""

    def __init__(
        self,
        allowed_origin: Optional[str] = None,
        allow_test_loopback: bool = False,
        test_fixture_origin: Optional[str] = None,
    ):
        self.allowed_origin = allowed_origin.lower() if allowed_origin else None
        self.allow_test_loopback = allow_test_loopback
        self.test_fixture_origin = test_fixture_origin.lower() if test_fixture_origin else None

    async def handle_route(self, route: Route) -> None:
        """Inspect and enforce network security on each browser-initiated request."""
        request = route.request
        url = request.url
        resource_type = request.resource_type

        # 1. Block prohibited resource types (e.g. WebSockets)
        if resource_type in BLOCKED_RESOURCE_TYPES:
            logger.debug("Aborted request with blocked resource type '%s': %s", resource_type, url)
            await route.abort("blockedbyclient")
            return

        try:
            parts = urlsplit(url)
        except Exception:
            await route.abort("blockedbyclient")
            return

        scheme = parts.scheme.lower()

        # 2. Scheme enforcement
        if scheme not in ALLOWED_BROWSER_SCHEMES:
            logger.warning("Aborted request with disallowed scheme '%s': %s", scheme, url)
            await route.abort("accessdenied")
            return

        # Data, blob, and about schemes do not make network calls
        if scheme in ("data", "blob", "about"):
            await route.continue_()
            return

        hostname = (parts.hostname or "").lower().strip()
        if not hostname:
            await route.abort("accessdenied")
            return

        # 3. Check test loopback exception
        if self.allow_test_loopback and self.test_fixture_origin:
            req_origin = f"{scheme}://{parts.netloc}".lower()
            if req_origin == self.test_fixture_origin or hostname in ("127.0.0.1", "localhost", "testclient"):
                await route.continue_()
                return

        # 4. Hostname & Cloud Metadata checks
        if hostname in FORBIDDEN_HOSTNAMES or hostname.endswith(".internal"):
            logger.warning("SSRF Guard: Aborted request to forbidden host '%s': %s", hostname, url)
            await route.abort("accessdenied")
            return

        # 5. Resolve DNS and verify all returned IP addresses are publicly routable
        try:
            resolve_and_validate_host(hostname)
        except Exception as exc:
            logger.warning("SSRF Guard: Aborted request to non-public/private host '%s': %s", hostname, exc)
            await route.abort("accessdenied")
            return

        # Request is verified safe
        await route.continue_()
