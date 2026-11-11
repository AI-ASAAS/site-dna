"""robots.txt fetching and policy exposure (Phase 2).

Uses `urllib.robotparser` for matching, with explicit status reporting so callers
can distinguish a missing policy (allow all) from a fetch failure (allow with warning).
"""

from enum import Enum
from typing import Optional
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

from site_dna.core.logging import get_logger
from site_dna.services.http_client import USER_AGENT

logger = get_logger("crawler.robots")


class RobotsStatus(str, Enum):
    found = "found"
    missing = "missing"
    error = "error"


class RobotsTxt:
    """Parsed robots.txt policy for a single origin."""

    def __init__(
        self,
        origin: str,
        status: RobotsStatus,
        *,
        user_agent: str = USER_AGENT,
        parser: Optional[RobotFileParser] = None,
        crawl_delay: Optional[float] = None,
        sitemaps: Optional[list[str]] = None,
        warning: Optional[str] = None,
    ):
        self.origin = origin
        self.status = status
        self.user_agent = user_agent
        self._parser = parser
        self.crawl_delay = crawl_delay
        self.sitemaps = sitemaps or []
        self.warning = warning

    @classmethod
    def from_text(cls, origin: str, text: str, *, user_agent: str = USER_AGENT) -> "RobotsTxt":
        parser = RobotFileParser()
        parser.parse(text.splitlines())

        delay = parser.crawl_delay(user_agent)
        sitemaps: list[str] = []
        for raw_line in text.splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            field, value = line.split(":", 1)
            if field.strip().lower() == "sitemap" and value.strip():
                sitemaps.append(value.strip())

        return cls(
            origin,
            RobotsStatus.found,
            user_agent=user_agent,
            parser=parser,
            crawl_delay=float(delay) if delay is not None else None,
            sitemaps=sitemaps,
        )

    def can_fetch(self, url: str) -> bool:
        """Return True when the URL may be fetched under this policy."""
        if self.status != RobotsStatus.found or self._parser is None:
            return True
        return self._parser.can_fetch(self.user_agent, url)


async def fetch_robots(client, origin: str, *, user_agent: str = USER_AGENT) -> RobotsTxt:
    """Fetch and parse robots.txt for an origin via the safe HTTP client.

    - 2xx: parse rules (`found`).
    - 4xx: no policy, allow all (`missing`).
    - 5xx or network error: allow all but report `error` and a warning.
    """
    robots_url = urljoin(origin, "/robots.txt")
    try:
        response = await client.safe_get(robots_url)
    except Exception as e:  # robots failures must never abort a crawl
        logger.warning("Failed to fetch robots.txt from %s: %s", robots_url, e)
        return RobotsTxt(origin, RobotsStatus.error, user_agent=user_agent, warning=str(e))

    if response.status_code == 200:
        logger.info("Fetched robots.txt from %s", robots_url)
        return RobotsTxt.from_text(origin, response.text, user_agent=user_agent)

    if 400 <= response.status_code < 500:
        logger.info("robots.txt returned %d at %s: allowing all", response.status_code, robots_url)
        return RobotsTxt(origin, RobotsStatus.missing, user_agent=user_agent)

    warning = f"robots.txt returned HTTP {response.status_code}; allowing all with warning"
    logger.warning("%s (%s)", warning, robots_url)
    return RobotsTxt(origin, RobotsStatus.error, user_agent=user_agent, warning=warning)
