"""Sitemap discovery and parsing for the Phase 7 SEO analyzer."""

import gzip
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urljoin

from defusedxml import ElementTree

from site_dna.analyzers.seo.rules import (
    SITEMAP_MAX_BYTES,
    SITEMAP_MAX_DEPTH,
    SITEMAP_MAX_URLS,
)
from site_dna.core.logging import get_logger

logger = get_logger("analyzers.seo.sitemap")


class SitemapStatus(str, Enum):
    """Outcome of sitemap discovery."""

    found = "found"
    missing = "missing"
    error = "error"


@dataclass
class SitemapResult:
    """Parsed sitemap URLs plus discovery metadata."""

    status: SitemapStatus
    urls: list[str] = field(default_factory=list)
    source: str | None = None
    warnings: list[str] = field(default_factory=list)
    truncated: bool = False


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _extract_locs(xml_bytes: bytes) -> tuple[list[str], bool]:
    """Return ``(locations, is_index)`` from a urlset or sitemapindex document."""
    root = ElementTree.fromstring(xml_bytes)
    root_name = _local_name(root.tag)
    if root_name not in {"urlset", "sitemapindex"}:
        raise ValueError(f"unexpected sitemap root element: {root_name}")

    locations = [
        (element.text or "").strip()
        for element in root.iter()
        if _local_name(element.tag) == "loc" and (element.text or "").strip()
    ]
    return locations, root_name == "sitemapindex"


async def _fetch_document(client, url: str) -> tuple[SitemapStatus, bytes | None, str | None]:
    try:
        response = await client.safe_get(url)
    except Exception as exc:
        return SitemapStatus.error, None, f"{url}: {exc}"

    if response.status_code == 404:
        return SitemapStatus.missing, None, None
    if response.status_code < 200 or response.status_code >= 300:
        return SitemapStatus.error, None, f"{url}: HTTP {response.status_code}"

    content = response.content
    if len(content) > SITEMAP_MAX_BYTES:
        return SitemapStatus.error, None, f"{url}: sitemap exceeds {SITEMAP_MAX_BYTES} bytes"
    if content[:2] == b"\x1f\x8b":
        try:
            content = gzip.decompress(content)
        except OSError as exc:
            return SitemapStatus.error, None, f"{url}: invalid gzip sitemap ({exc})"
        if len(content) > SITEMAP_MAX_BYTES:
            return SitemapStatus.error, None, f"{url}: decompressed sitemap exceeds {SITEMAP_MAX_BYTES} bytes"
    return SitemapStatus.found, content, None


async def fetch_sitemap(
    client,
    origin: str,
    declared_sitemaps: list[str] | None = None,
    *,
    max_urls: int = SITEMAP_MAX_URLS,
    max_depth: int = SITEMAP_MAX_DEPTH,
) -> SitemapResult:
    """Fetch and flatten a site's sitemap, following child indexes.

    Declared ``Sitemap:`` entries from robots.txt are tried first, followed by
    ``/sitemap.xml``. Only the first successful top-level document is used.
    """
    candidates: list[str] = []
    for candidate in [*(declared_sitemaps or []), urljoin(origin, "/sitemap.xml")]:
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    root_status = SitemapStatus.missing
    root_url: str | None = None
    root_locations: list[str] = []
    warnings: list[str] = []

    for candidate in candidates:
        status, content, warning = await _fetch_document(client, candidate)
        if status is SitemapStatus.error:
            root_status = SitemapStatus.error
            if warning:
                warnings.append(warning)
            continue
        if status is SitemapStatus.missing:
            continue
        try:
            root_locations, is_index = _extract_locs(content or b"")
        except Exception as exc:
            root_status = SitemapStatus.error
            warnings.append(f"{candidate}: {exc}")
            continue
        root_status = SitemapStatus.found
        root_url = candidate
        if not is_index:
            return SitemapResult(
                status=root_status,
                urls=root_locations[:max_urls],
                source=root_url,
                warnings=warnings,
                truncated=len(root_locations) > max_urls,
            )
        break

    if root_status is not SitemapStatus.found or root_url is None:
        return SitemapResult(status=root_status, warnings=warnings)

    urls: list[str] = []
    truncated = False
    queue: list[tuple[str, int]] = [(location, 1) for location in root_locations]
    seen: set[str] = set()

    while queue:
        child_url, depth = queue.pop(0)
        if child_url in seen or depth > max_depth:
            continue
        seen.add(child_url)
        status, content, warning = await _fetch_document(client, child_url)
        if status is not SitemapStatus.found:
            if warning:
                warnings.append(warning)
            continue
        try:
            locations, is_index = _extract_locs(content or b"")
        except Exception as exc:
            warnings.append(f"{child_url}: {exc}")
            continue
        if is_index:
            queue.extend((location, depth + 1) for location in locations)
            continue
        for location in locations:
            if len(urls) >= max_urls:
                truncated = True
                queue.clear()
                break
            urls.append(location)

    return SitemapResult(
        status=SitemapStatus.found,
        urls=urls,
        source=root_url,
        warnings=warnings,
        truncated=truncated,
    )
