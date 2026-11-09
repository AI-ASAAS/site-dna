"""Sitemap discovery and parsing using defusedxml for XXE protection."""

from typing import Optional
from urllib.parse import urljoin

import defusedxml.ElementTree as ET

from site_dna.core.logging import get_logger
from site_dna.discovery.http_client import FetchError, HttpResponseData, SecureHttpClient
from site_dna.discovery.url_validator import is_same_origin, normalize_url

logger = get_logger("discovery.sitemap")


class SitemapResult:
    """Outcome of sitemap discovery and URL extraction."""

    def __init__(self):
        self.sitemap_found: bool = False
        self.sitemap_urls: list[str] = []
        self.discovered_page_urls: list[str] = []


def _extract_loc_values(xml_bytes: bytes, target_parent_tag: Optional[str] = None) -> list[str]:
    """Parse XML safely using defusedxml and extract <loc> text elements.

    Args:
        xml_bytes: Raw XML document bytes.
        target_parent_tag: If specified, only extract <loc> whose parent tag matches (e.g. 'url' or 'sitemap').
    """
    locs: list[str] = []
    try:
        root = ET.fromstring(xml_bytes)
    except Exception as e:
        logger.debug("Failed to parse XML: %s", e)
        return []

    for parent in root.iter():
        parent_tag = parent.tag.split("}")[-1].lower()
        if target_parent_tag and parent_tag != target_parent_tag:
            continue

        for child in parent:
            child_tag = child.tag.split("}")[-1].lower()
            if child_tag == "loc" and child.text:
                val = child.text.strip()
                if val:
                    locs.append(val)

    # Fallback if structure is flat
    if not locs and not target_parent_tag:
        for elem in root.iter():
            tag = elem.tag.split("}")[-1].lower()
            if tag == "loc" and elem.text:
                val = elem.text.strip()
                if val:
                    locs.append(val)

    return locs


def _is_sitemap_index(xml_bytes: bytes) -> bool:
    """Check if the XML document is a sitemap index file."""
    try:
        root = ET.fromstring(xml_bytes)
        tag = root.tag.split("}")[-1].lower()
        return "sitemapindex" in tag
    except Exception:
        return False


async def discover_sitemaps(
    client: SecureHttpClient,
    origin: str,
    robots_sitemaps: Optional[list[str]] = None,
    max_urls: int = 200,
) -> SitemapResult:
    """Discover sitemaps from robots.txt or common locations, and collect page URLs safely.

    Args:
        client: Secure HTTP client.
        origin: The canonical website origin (e.g. 'https://example.com').
        robots_sitemaps: Sitemap URLs declared in robots.txt.
        max_urls: Maximum candidate page URLs to extract.

    Returns:
        SitemapResult containing found sitemaps and extracted page URLs.
    """
    result = SitemapResult()
    candidates_to_try: list[str] = []

    if robots_sitemaps:
        candidates_to_try.extend(robots_sitemaps)

    # Standard well-known fallbacks
    candidates_to_try.append(urljoin(origin, "/sitemap.xml"))
    candidates_to_try.append(urljoin(origin, "/sitemap_index.xml"))

    # Deduplicate candidate URLs while preserving order
    seen_sitemap_candidates: set[str] = set()
    sitemaps_to_fetch: list[str] = []
    for s_url in candidates_to_try:
        try:
            norm = normalize_url(s_url)
            if norm not in seen_sitemap_candidates and is_same_origin(origin, norm):
                seen_sitemap_candidates.add(norm)
                sitemaps_to_fetch.append(norm)
        except Exception:
            continue

    discovered_pages: set[str] = set()
    sub_sitemaps_visited: set[str] = set()

    for sitemap_url in sitemaps_to_fetch:
        if len(discovered_pages) >= max_urls:
            break
        if sitemap_url in sub_sitemaps_visited:
            continue

        try:
            resp: HttpResponseData = await client.fetch(sitemap_url, allow_xml=True)
            if resp.status_code != 200:
                continue

            result.sitemap_found = True
            if sitemap_url not in result.sitemap_urls:
                result.sitemap_urls.append(sitemap_url)
            sub_sitemaps_visited.add(sitemap_url)

            if _is_sitemap_index(resp.content):
                # Nested sitemaps: extract child sitemaps (bounded to 3)
                sub_locs = _extract_loc_values(resp.content, target_parent_tag="sitemap")
                for sub_loc in sub_locs[:3]:
                    try:
                        norm_sub = normalize_url(sub_loc)
                        if norm_sub not in sub_sitemaps_visited and is_same_origin(origin, norm_sub):
                            sub_resp = await client.fetch(norm_sub, allow_xml=True)
                            if sub_resp.status_code == 200:
                                result.sitemap_urls.append(norm_sub)
                                sub_sitemaps_visited.add(norm_sub)
                                page_locs = _extract_loc_values(sub_resp.content, target_parent_tag="url")
                                for p_loc in page_locs:
                                    if len(discovered_pages) >= max_urls:
                                        break
                                    try:
                                        norm_page = normalize_url(p_loc)
                                        if is_same_origin(origin, norm_page):
                                            discovered_pages.add(norm_page)
                                    except Exception:
                                        continue
                    except Exception as e:
                        logger.debug("Failed fetching sub-sitemap %s: %s", sub_loc, e)
            else:
                # Direct urlset
                page_locs = _extract_loc_values(resp.content, target_parent_tag="url")
                for p_loc in page_locs:
                    if len(discovered_pages) >= max_urls:
                        break
                    try:
                        norm_page = normalize_url(p_loc)
                        if is_same_origin(origin, norm_page):
                            discovered_pages.add(norm_page)
                    except Exception:
                        continue

        except FetchError as e:
            logger.debug("Sitemap not found or fetch error at %s: %s", sitemap_url, e)
        except Exception as e:
            logger.debug("Unexpected error reading sitemap %s: %s", sitemap_url, e)

    result.discovered_page_urls = sorted(discovered_pages)
    logger.info(
        "Sitemap discovery completed: found=%s, count=%d pages",
        result.sitemap_found,
        len(result.discovered_page_urls),
    )
    return result
