"""Bounded BFS crawl manager for the Website Intelligence MVP (Phase 2).

A deterministic BFS loop over the safe HTTP client enforces page, depth, scope,
robots, and URL-validation limits before every fetch.
"""

import ipaddress
import time
from collections import deque
from enum import Enum
from typing import Optional
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup
from pydantic import BaseModel

from site_dna.core.logging import get_logger
from site_dna.crawler.categorizer import categorize_url
from site_dna.crawler.robots import RobotsTxt, fetch_robots
from site_dna.services.http_client import USER_AGENT, FetchError
from site_dna.services.normalizer import canonicalize_url, is_non_html_url, registrable_domain
from site_dna.services.security import UrlRejected, validate_url

logger = get_logger("crawler.crawl_manager")

class DiscoveredStatus(str, Enum):
    fetched = "fetched"
    skipped_robots = "skipped_robots"
    skipped_scope = "skipped_scope"
    skipped_limit = "skipped_limit"
    failed = "failed"


class DiscoveredUrl(BaseModel):
    """A URL encountered during a crawl and the outcome of processing it."""

    url: str
    depth: int
    discovered_from: Optional[str] = None
    category: str = "other"
    status: DiscoveredStatus = DiscoveredStatus.fetched


def _origin_of(scheme: str, host: str, port: int) -> str:
    default_port = 80 if scheme == "http" else 443
    try:
        is_ipv6 = isinstance(ipaddress.ip_address(host), ipaddress.IPv6Address)
    except ValueError:
        is_ipv6 = False
    rendered_host = f"[{host}]" if is_ipv6 else host
    if port != default_port:
        return f"{scheme}://{rendered_host}:{port}"
    return f"{scheme}://{rendered_host}"


class CrawlManager:
    """Deterministic BFS crawler bounded by pages, depth, scope, and wall clock."""

    def __init__(
        self,
        *,
        client,
        max_pages: int = 20,
        max_depth: int = 2,
        max_total_seconds: float = 300.0,
        include_external: bool = False,
        user_agent: str = USER_AGENT,
        validator=None,
        robots: Optional[RobotsTxt] = None,
        respect_robots: bool = True,
        categorizer=categorize_url,
    ):
        self._client = client
        self._max_pages = max_pages
        self._max_depth = max_depth
        self._max_total_seconds = max_total_seconds
        self._include_external = include_external
        self._user_agent = user_agent
        self._validator = validator or validate_url
        self._robots = robots
        self._respect_robots = respect_robots
        self._categorizer = categorizer

    def _record(
        self,
        url: str,
        depth: int,
        discovered_from: Optional[str],
        status: DiscoveredStatus,
        category: Optional[str] = None,
    ) -> DiscoveredUrl:
        return DiscoveredUrl(
            url=url,
            depth=depth,
            discovered_from=discovered_from,
            category=category or self._categorizer(url, depth=depth),
            status=status,
        )

    async def crawl(self, seed_url: str) -> list[DiscoveredUrl]:
        """Crawl from seed_url and return every discovered URL with its outcome."""
        validated_seed = await self._validator(seed_url)
        seed = validated_seed.url
        origin = _origin_of(validated_seed.scheme, validated_seed.host, validated_seed.port)
        seed_domain = registrable_domain(validated_seed.host)

        robots: Optional[RobotsTxt] = self._robots
        if robots is None and self._respect_robots:
            robots = await fetch_robots(self._client, origin, user_agent=self._user_agent)

        queue: deque[tuple[str, int, Optional[str]]] = deque([(seed, 0, None)])
        seen: set[str] = {canonicalize_url(seed)}
        discovered: list[DiscoveredUrl] = []
        fetched_count = 0
        deadline = time.monotonic() + self._max_total_seconds

        while queue:
            if time.monotonic() >= deadline:
                for remaining_url, remaining_depth, remaining_from in queue:
                    discovered.append(
                        self._record(
                            remaining_url,
                            remaining_depth,
                            remaining_from,
                            DiscoveredStatus.skipped_limit,
                        )
                    )
                queue.clear()
                break

            url, depth, discovered_from = queue.popleft()

            if depth > self._max_depth:
                discovered.append(
                    self._record(url, depth, discovered_from, DiscoveredStatus.skipped_limit)
                )
                continue

            if robots is not None and not robots.can_fetch(url):
                logger.info("Skipping robots-disallowed URL: %s", url)
                discovered.append(
                    self._record(url, depth, discovered_from, DiscoveredStatus.skipped_robots)
                )
                continue

            if fetched_count >= self._max_pages:
                discovered.append(
                    self._record(url, depth, discovered_from, DiscoveredStatus.skipped_limit)
                )
                continue

            try:
                response = await self._client.safe_get(url)
            except (UrlRejected, FetchError) as e:
                logger.warning("Fetch failed for %s: %s", url, e)
                discovered.append(
                    self._record(url, depth, discovered_from, DiscoveredStatus.failed)
                )
                continue

            fetched_count += 1

            if response.status_code >= 400:
                logger.warning("HTTP %d for %s", response.status_code, url)
                discovered.append(
                    self._record(url, depth, discovered_from, DiscoveredStatus.failed)
                )
                continue

            content_type = response.headers.get("content-type", "").lower()
            if "html" not in content_type and "xhtml" not in content_type:
                discovered.append(
                    self._record(url, depth, discovered_from, DiscoveredStatus.skipped_scope)
                )
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            h1_tag = soup.find("h1")
            h1 = h1_tag.get_text(" ", strip=True) if h1_tag else ""
            category = self._categorizer(response.final_url, depth=depth, title=title, h1=h1)
            discovered.append(
                self._record(
                    response.final_url,
                    depth,
                    discovered_from,
                    DiscoveredStatus.fetched,
                    category=category,
                )
            )

            if depth >= self._max_depth:
                continue

            for anchor in soup.find_all("a", href=True):
                href = anchor["href"].strip()
                if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
                    continue

                absolute = urljoin(response.final_url, href)
                parts = urlsplit(absolute)
                if parts.scheme not in {"http", "https"}:
                    continue

                canonical = canonicalize_url(absolute)
                host = (parts.hostname or "").lower()

                if not self._include_external and registrable_domain(host) != seed_domain:
                    discovered.append(
                        self._record(canonical, depth + 1, url, DiscoveredStatus.skipped_scope)
                    )
                    continue

                if is_non_html_url(canonical):
                    discovered.append(
                        self._record(canonical, depth + 1, url, DiscoveredStatus.skipped_scope)
                    )
                    continue

                if canonical in seen:
                    continue

                seen.add(canonical)
                queue.append((canonical, depth + 1, url))

        return discovered
