"""Technical SEO analyzer for the Website Intelligence MVP (Phase 7)."""

import asyncio
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

from selectolax.lexbor import LexborHTMLParser

from site_dna.analyzers.seo.rules import (
    BROKEN_LINK_CONCURRENCY,
    BROKEN_LINK_MAX_CHECKS,
    META_DESCRIPTION_MAX_CHARS,
    META_DESCRIPTION_MIN_CHARS,
    TITLE_MAX_CHARS,
    TITLE_MIN_CHARS,
)
from site_dna.analyzers.seo.sitemap import SitemapResult, SitemapStatus, fetch_sitemap
from site_dna.core.logging import get_logger
from site_dna.models.common import CheckStatus, ModuleError, ModuleResult, ModuleStatus
from site_dna.models.page import LinkItem, PageData
from site_dna.models.seo import CheckRecord, SeoAnalysis, SeoIssue, SeoSummary
from site_dna.services.normalizer import canonicalize_url

logger = get_logger("analyzers.seo")

_CONFIDENCE_HIGH = "high"
_CONFIDENCE_MEDIUM = "medium"


@dataclass
class BrokenLink:
    """A link target that failed the broken-link check."""

    url: str
    status_code: int | None = None
    error: str | None = None
    found_on: list[str] | None = None


def _tree(html: str | None) -> LexborHTMLParser | None:
    if not html:
        return None
    try:
        return LexborHTMLParser(html)
    except Exception:
        return None


def _text(node) -> str | None:
    if node is None:
        return None
    text = (node.text() or "").strip()
    return text or None


def _check(
    rule_id: str,
    *,
    scope: str,
    status: CheckStatus,
    url: str | None = None,
    value=None,
    message: str | None = None,
    threshold=None,
    confidence: str | None = None,
) -> CheckRecord:
    return CheckRecord(
        id=rule_id,
        scope=scope,
        url=url,
        status=status,
        value=value,
        message=message,
        threshold=threshold,
        confidence=confidence,
    )


def _meta_content(tree: LexborHTMLParser, *, name: str | None = None, prop: str | None = None) -> str | None:
    for node in tree.css("meta"):
        attrs = node.attributes
        if name is not None and (attrs.get("name") or "").lower() == name:
            content = (attrs.get("content") or "").strip()
            if content:
                return content
        if prop is not None and (attrs.get("property") or "").lower() == prop:
            content = (attrs.get("content") or "").strip()
            if content:
                return content
    return None


def _canonical_hrefs(tree: LexborHTMLParser) -> list[str]:
    hrefs: list[str] = []
    for node in tree.css("link"):
        rel = (node.attributes.get("rel") or "").lower().split()
        if "canonical" in rel:
            href = (node.attributes.get("href") or "").strip()
            if href:
                hrefs.append(href)
    return hrefs


def _heading_outline(page: PageData, tree: LexborHTMLParser | None) -> list[tuple[int, str]]:
    if page.heading_outline:
        return [(item.level, item.text) for item in page.heading_outline]
    if tree is None:
        return []
    outline: list[tuple[int, str]] = []
    for node in tree.css("h1, h2, h3"):
        level = int(node.tag[1])
        text = _text(node) or ""
        outline.append((level, text))
    return outline


def _page_checks(page: PageData) -> list[CheckRecord]:
    tree = _tree(page.raw_html)
    checks: list[CheckRecord] = []

    title = page.title if page.title is not None else _text(tree.css_first("title") if tree else None)
    title = title.strip() if isinstance(title, str) else title
    if not title:
        checks.append(
            _check(
                "title",
                scope="page",
                url=page.url,
                status=CheckStatus.failed,
                message="Page title is missing.",
                threshold={"min": TITLE_MIN_CHARS, "max": TITLE_MAX_CHARS},
                confidence=_CONFIDENCE_HIGH,
            )
        )
    elif len(title) < TITLE_MIN_CHARS or len(title) > TITLE_MAX_CHARS:
        checks.append(
            _check(
                "title",
                scope="page",
                url=page.url,
                status=CheckStatus.warning,
                value=title,
                message=f"Title length is {len(title)} characters; expected {TITLE_MIN_CHARS}-{TITLE_MAX_CHARS}.",
                threshold={"min": TITLE_MIN_CHARS, "max": TITLE_MAX_CHARS},
                confidence=_CONFIDENCE_HIGH,
            )
        )
    else:
        checks.append(
            _check(
                "title",
                scope="page",
                url=page.url,
                status=CheckStatus.passed,
                value=title,
                threshold={"min": TITLE_MIN_CHARS, "max": TITLE_MAX_CHARS},
                confidence=_CONFIDENCE_HIGH,
            )
        )

    if tree is None:
        checks.append(
            _check(
                "meta_description",
                scope="page",
                url=page.url,
                status=CheckStatus.not_available,
                message="Raw HTML was not captured; meta description could not be inspected.",
                confidence=_CONFIDENCE_MEDIUM,
            )
        )
    else:
        description = _meta_content(tree, name="description")
        threshold = {"min": META_DESCRIPTION_MIN_CHARS, "max": META_DESCRIPTION_MAX_CHARS}
        if not description:
            checks.append(
                _check(
                    "meta_description",
                    scope="page",
                    url=page.url,
                    status=CheckStatus.failed,
                    message="Meta description is missing.",
                    threshold=threshold,
                    confidence=_CONFIDENCE_HIGH,
                )
            )
        elif len(description) < META_DESCRIPTION_MIN_CHARS or len(description) > META_DESCRIPTION_MAX_CHARS:
            checks.append(
                _check(
                    "meta_description",
                    scope="page",
                    url=page.url,
                    status=CheckStatus.warning,
                    value=description,
                    message=(
                        f"Meta description length is {len(description)} characters; "
                        f"expected {META_DESCRIPTION_MIN_CHARS}-{META_DESCRIPTION_MAX_CHARS}."
                    ),
                    threshold=threshold,
                    confidence=_CONFIDENCE_HIGH,
                )
            )
        else:
            checks.append(
                _check(
                    "meta_description",
                    scope="page",
                    url=page.url,
                    status=CheckStatus.passed,
                    value=description,
                    threshold=threshold,
                    confidence=_CONFIDENCE_HIGH,
                )
            )

    if tree is None and not page.http_headers:
        checks.append(
            _check(
                "meta_robots",
                scope="page",
                url=page.url,
                status=CheckStatus.not_available,
                message="Raw HTML and response headers were not captured.",
                confidence=_CONFIDENCE_MEDIUM,
            )
        )
    else:
        directives: list[str] = []
        if tree is not None:
            for name in ("robots", "googlebot"):
                content = _meta_content(tree, name=name)
                if content:
                    directives.append(content.lower())
        header = page.http_headers.get("x-robots-tag") or page.http_headers.get("X-Robots-Tag")
        if header:
            directives.append(header.lower())
        combined = ",".join(directives)
        if not directives:
            checks.append(
                _check(
                    "meta_robots",
                    scope="page",
                    url=page.url,
                    status=CheckStatus.not_available,
                    message="No robots meta tag or X-Robots-Tag header was present; this is normal.",
                    confidence=_CONFIDENCE_HIGH,
                )
            )
        elif "noindex" in combined or "none" in combined or "nofollow" in combined:
            checks.append(
                _check(
                    "meta_robots",
                    scope="page",
                    url=page.url,
                    status=CheckStatus.warning,
                    value=combined,
                    message="Page declares restrictive robots directives.",
                    confidence=_CONFIDENCE_HIGH,
                )
            )
        else:
            checks.append(
                _check(
                    "meta_robots",
                    scope="page",
                    url=page.url,
                    status=CheckStatus.passed,
                    value=combined,
                    confidence=_CONFIDENCE_HIGH,
                )
            )

    if tree is None:
        checks.append(
            _check(
                "canonical",
                scope="page",
                url=page.url,
                status=CheckStatus.not_available,
                message="Raw HTML was not captured; canonical link could not be inspected.",
                confidence=_CONFIDENCE_MEDIUM,
            )
        )
    else:
        hrefs = _canonical_hrefs(tree)
        if not hrefs:
            checks.append(
                _check(
                    "canonical",
                    scope="page",
                    url=page.url,
                    status=CheckStatus.warning,
                    message="Canonical link is missing.",
                    confidence=_CONFIDENCE_MEDIUM,
                )
            )
        elif len(hrefs) > 1:
            checks.append(
                _check(
                    "canonical",
                    scope="page",
                    url=page.url,
                    status=CheckStatus.failed,
                    value=hrefs,
                    message="Multiple canonical links were found; search engines may ignore them.",
                    confidence=_CONFIDENCE_HIGH,
                )
            )
        else:
            resolved = urljoin(page.final_url or page.url, hrefs[0])
            expected = canonicalize_url(page.final_url or page.url)
            actual = canonicalize_url(resolved)
            if actual != expected:
                checks.append(
                    _check(
                        "canonical",
                        scope="page",
                        url=page.url,
                        status=CheckStatus.warning,
                        value=resolved,
                        message="Canonical URL does not match the crawled page.",
                        confidence=_CONFIDENCE_MEDIUM,
                    )
                )
            else:
                checks.append(
                    _check(
                        "canonical",
                        scope="page",
                        url=page.url,
                        status=CheckStatus.passed,
                        value=resolved,
                        confidence=_CONFIDENCE_HIGH,
                    )
                )

    if tree is None:
        checks.append(
            _check(
                "open_graph",
                scope="page",
                url=page.url,
                status=CheckStatus.not_available,
                message="Raw HTML was not captured; Open Graph tags could not be inspected.",
                confidence=_CONFIDENCE_MEDIUM,
            )
        )
    else:
        required = ("og:title", "og:description", "og:image")
        optional = ("og:url", "og:type")
        tags = {
            prop: _meta_content(tree, prop=prop)
            for prop in (*required, *optional)
            if _meta_content(tree, prop=prop)
        }
        present = [prop for prop in required if prop in tags]
        missing = [prop for prop in required if prop not in tags]
        if not tags:
            checks.append(
                _check(
                    "open_graph",
                    scope="page",
                    url=page.url,
                    status=CheckStatus.not_available,
                    value={"present": [], "missing": missing},
                    message="No Open Graph tags were found.",
                    confidence=_CONFIDENCE_MEDIUM,
                )
            )
        elif missing:
            checks.append(
                _check(
                    "open_graph",
                    scope="page",
                    url=page.url,
                    status=CheckStatus.warning,
                    value={"present": present, "missing": missing, "tags": tags},
                    message=f"Open Graph tags are incomplete: {', '.join(missing)}.",
                    confidence=_CONFIDENCE_MEDIUM,
                )
            )
        else:
            checks.append(
                _check(
                    "open_graph",
                    scope="page",
                    url=page.url,
                    status=CheckStatus.passed,
                    value={"present": present, "missing": [], "tags": tags},
                    confidence=_CONFIDENCE_HIGH,
                )
            )

    h1s = page.headings.h1
    if tree is not None and not h1s:
        h1s = [text for level, text in _heading_outline(page, tree) if level == 1]
    if not h1s and tree is None and not page.heading_outline:
        checks.append(
            _check(
                "headings",
                scope="page",
                url=page.url,
                status=CheckStatus.not_available,
                message="Heading data was not captured.",
                confidence=_CONFIDENCE_MEDIUM,
            )
        )
    elif not h1s:
        checks.append(
            _check(
                "headings",
                scope="page",
                url=page.url,
                status=CheckStatus.failed,
                value={"h1_count": 0},
                message="Page has no H1 heading.",
                threshold={"h1": 1},
                confidence=_CONFIDENCE_HIGH,
            )
        )
    elif len(h1s) > 1:
        checks.append(
            _check(
                "headings",
                scope="page",
                url=page.url,
                status=CheckStatus.warning,
                value={"h1_count": len(h1s), "h1": h1s},
                message="Page has multiple H1 headings.",
                threshold={"h1": 1},
                confidence=_CONFIDENCE_HIGH,
            )
        )
    else:
        checks.append(
            _check(
                "headings",
                scope="page",
                url=page.url,
                status=CheckStatus.passed,
                value={"h1_count": 1, "h1": h1s},
                threshold={"h1": 1},
                confidence=_CONFIDENCE_HIGH,
            )
        )

    outline = _heading_outline(page, tree)
    if not outline:
        checks.append(
            _check(
                "heading_hierarchy",
                scope="page",
                url=page.url,
                status=CheckStatus.not_available,
                message="No heading outline was captured.",
                confidence=_CONFIDENCE_MEDIUM,
            )
        )
    else:
        skipped: list[str] = []
        previous = None
        for level, text in outline:
            if previous is not None and level - previous > 1:
                skipped.append(f"h{previous}->h{level}: {text}")
            previous = level
        if skipped:
            checks.append(
                _check(
                    "heading_hierarchy",
                    scope="page",
                    url=page.url,
                    status=CheckStatus.warning,
                    value=skipped,
                    message="Heading levels skip downward.",
                    confidence=_CONFIDENCE_MEDIUM,
                )
            )
        else:
            checks.append(
                _check(
                    "heading_hierarchy",
                    scope="page",
                    url=page.url,
                    status=CheckStatus.passed,
                    value=[f"h{level}: {text}" for level, text in outline],
                    confidence=_CONFIDENCE_HIGH,
                )
            )

    if page.images:
        missing_alt = [image.src for image in page.images if image.alt is None]
        decorative = [image.src for image in page.images if image.alt == ""]
        non_empty = [image.src for image in page.images if image.alt and image.alt.strip()]
        image_count = len(page.images)
    elif tree is not None:
        missing_alt = []
        decorative = []
        non_empty = []
        image_count = 0
        for node in tree.css("img"):
            image_count += 1
            src = node.attributes.get("src") or ""
            alt = node.attributes.get("alt")
            if alt is None:
                missing_alt.append(src)
            elif alt.strip():
                non_empty.append(src)
            else:
                decorative.append(src)
    else:
        missing_alt = []
        decorative = []
        non_empty = []
        image_count = 0

    image_value = {
        "images": image_count,
        "non_empty_alt": len(non_empty),
        "missing_alt": len(missing_alt),
        "decorative": len(decorative),
        "examples": missing_alt[:50],
    }
    if missing_alt:
        checks.append(
            _check(
                "images_alt",
                scope="page",
                url=page.url,
                status=CheckStatus.failed,
                value=image_value,
                message="One or more images are missing the alt attribute.",
                confidence=_CONFIDENCE_HIGH,
            )
        )
    else:
        checks.append(
            _check(
                "images_alt",
                scope="page",
                url=page.url,
                status=CheckStatus.passed,
                value=image_value,
                confidence=_CONFIDENCE_HIGH,
            )
        )

    language = page.language
    if tree is not None:
        html_node = tree.css_first("html")
        if html_node is not None:
            language = (html_node.attributes.get("lang") or "").strip() or language
    if language is None and tree is None:
        checks.append(
            _check(
                "lang",
                scope="page",
                url=page.url,
                status=CheckStatus.not_available,
                message="Raw HTML was not captured; language could not be inspected.",
                confidence=_CONFIDENCE_MEDIUM,
            )
        )
    elif not language:
        checks.append(
            _check(
                "lang",
                scope="page",
                url=page.url,
                status=CheckStatus.warning,
                message="html lang attribute is missing.",
                confidence=_CONFIDENCE_HIGH,
            )
        )
    else:
        checks.append(
            _check(
                "lang",
                scope="page",
                url=page.url,
                status=CheckStatus.passed,
                value=language,
                confidence=_CONFIDENCE_HIGH,
            )
        )

    if tree is None:
        checks.append(
            _check(
                "viewport",
                scope="page",
                url=page.url,
                status=CheckStatus.not_available,
                message="Raw HTML was not captured; viewport could not be inspected.",
                confidence=_CONFIDENCE_MEDIUM,
            )
        )
    else:
        viewport = _meta_content(tree, name="viewport")
        if not viewport:
            checks.append(
                _check(
                    "viewport",
                    scope="page",
                    url=page.url,
                    status=CheckStatus.warning,
                    message="Viewport meta tag is missing.",
                    confidence=_CONFIDENCE_HIGH,
                )
            )
        else:
            checks.append(
                _check(
                    "viewport",
                    scope="page",
                    url=page.url,
                    status=CheckStatus.passed,
                    value=viewport,
                    confidence=_CONFIDENCE_HIGH,
                )
            )

    return checks


def _origin(pages: list[PageData], robots) -> str:
    if robots is not None and getattr(robots, "origin", None):
        return robots.origin
    if pages:
        parts = urlsplit(pages[0].final_url or pages[0].url)
        if parts.scheme and parts.netloc:
            return f"{parts.scheme}://{parts.netloc}"
    return ""


def _site_checks(
    pages: list[PageData],
    *,
    robots,
    sitemap: SitemapResult | None,
    broken_links: list[BrokenLink] | None,
    broken_checked: int,
    broken_truncated: bool,
    broken_warnings: list[str] | None = None,
    link_total: int = 0,
) -> list[CheckRecord]:
    origin = _origin(pages, robots)
    checks: list[CheckRecord] = []

    if robots is None:
        checks.append(
            _check(
                "robots_txt",
                scope="site",
                status=CheckStatus.not_available,
                message="robots.txt was not fetched.",
                confidence=_CONFIDENCE_MEDIUM,
            )
        )
    elif robots.status.value == "found":
        blocked = bool(origin) and not robots.can_fetch(origin + "/")
        checks.append(
            _check(
                "robots_txt",
                scope="site",
                status=CheckStatus.warning if blocked else CheckStatus.passed,
                value={"status": robots.status.value, "sitemaps": robots.sitemaps},
                message="robots.txt disallows the scanned origin root." if blocked else None,
                confidence=_CONFIDENCE_HIGH,
            )
        )
    elif robots.status.value == "missing":
        checks.append(
            _check(
                "robots_txt",
                scope="site",
                status=CheckStatus.warning,
                value={"status": robots.status.value},
                message="robots.txt is missing; crawlers default to allow-all.",
                confidence=_CONFIDENCE_HIGH,
            )
        )
    else:
        checks.append(
            _check(
                "robots_txt",
                scope="site",
                status=CheckStatus.not_available,
                value={"status": robots.status.value, "warning": robots.warning},
                message="robots.txt could not be fetched; crawlers default to allow-all.",
                confidence=_CONFIDENCE_MEDIUM,
            )
        )

    if sitemap is None:
        checks.append(
            _check(
                "sitemap",
                scope="site",
                status=CheckStatus.not_available,
                message="Sitemap was not fetched.",
                confidence=_CONFIDENCE_MEDIUM,
            )
        )
    elif sitemap.status is SitemapStatus.found:
        checks.append(
            _check(
                "sitemap",
                scope="site",
                status=(
                    CheckStatus.failed
                    if not sitemap.urls
                    else CheckStatus.warning
                    if sitemap.truncated
                    else CheckStatus.passed
                ),
                value={
                    "urls": len(sitemap.urls),
                    "source": sitemap.source,
                    "truncated": sitemap.truncated,
                    "warnings": sitemap.warnings,
                },
                message=(
                    "Sitemap was found but contains no URLs."
                    if not sitemap.urls
                    else "Sitemap was truncated at the configured URL cap."
                    if sitemap.truncated
                    else None
                ),
                confidence=_CONFIDENCE_HIGH,
            )
        )
    elif sitemap.status is SitemapStatus.missing:
        checks.append(
            _check(
                "sitemap",
                scope="site",
                status=CheckStatus.warning,
                value={"status": sitemap.status.value, "warnings": sitemap.warnings},
                message="No sitemap was found at the declared locations or /sitemap.xml.",
                confidence=_CONFIDENCE_MEDIUM,
            )
        )
    else:
        checks.append(
            _check(
                "sitemap",
                scope="site",
                status=CheckStatus.failed,
                value={"status": sitemap.status.value, "warnings": sitemap.warnings},
                message="Sitemap exists but could not be parsed.",
                confidence=_CONFIDENCE_MEDIUM,
            )
        )

    status_counts = Counter(page.http_status for page in pages if page.http_status is not None)
    unknown = sum(1 for page in pages if page.http_status is None)
    bad = sum(count for status, count in status_counts.items() if status >= 400)
    redirects = sum(count for status, count in status_counts.items() if 300 <= status < 400)
    if not status_counts and unknown == 0:
        checks.append(
            _check(
                "status_codes",
                scope="site",
                status=CheckStatus.not_available,
                message="No HTTP status codes were captured.",
                confidence=_CONFIDENCE_MEDIUM,
            )
        )
    elif bad:
        checks.append(
            _check(
                "status_codes",
                scope="site",
                status=CheckStatus.failed,
                value={"counts": dict(sorted(status_counts.items())), "unknown": unknown},
                message=f"{bad} crawled page(s) returned HTTP 4xx/5xx.",
                confidence=_CONFIDENCE_HIGH,
            )
        )
    elif redirects or unknown:
        checks.append(
            _check(
                "status_codes",
                scope="site",
                status=CheckStatus.warning,
                value={"counts": dict(sorted(status_counts.items())), "unknown": unknown},
                message="Some crawled pages redirected or had no captured status.",
                confidence=_CONFIDENCE_MEDIUM,
            )
        )
    else:
        checks.append(
            _check(
                "status_codes",
                scope="site",
                status=CheckStatus.passed,
                value={"counts": dict(sorted(status_counts.items())), "unknown": unknown},
                confidence=_CONFIDENCE_HIGH,
            )
        )

    internal = sum(1 for page in pages for link in page.links if link.internal)
    external = sum(1 for page in pages for link in page.links if not link.internal)
    nofollow = sum(
        1 for page in pages for link in page.links if "nofollow" in (link.rel or "").lower().split()
    )
    unique_internal = {
        canonicalize_url(link.url) for page in pages for link in page.links if link.internal
    }
    unique_external = {
        canonicalize_url(link.url) for page in pages for link in page.links if not link.internal
    }
    other_schemes: Counter[str] = Counter()
    for page in pages:
        other_schemes.update(getattr(page, "non_http_link_counts", {}) or {})
    checks.append(
        _check(
            "links",
            scope="site",
            status=CheckStatus.passed,
            value={
                "total": internal + external,
                "internal": internal,
                "external": external,
                "nofollow": nofollow,
                "unique_internal": len(unique_internal),
                "unique_external": len(unique_external),
                "other_schemes": dict(other_schemes),
            },
            confidence=_CONFIDENCE_HIGH,
        )
    )

    if broken_links is None:
        checks.append(
            _check(
                "broken_links",
                scope="site",
                status=CheckStatus.not_available,
                message="Broken-link checking was not run.",
                confidence=_CONFIDENCE_MEDIUM,
            )
        )
    elif broken_links:
        checks.append(
            _check(
                "broken_links",
                scope="site",
                status=CheckStatus.failed,
                value={
                    "checked": broken_checked,
                    "broken": len(broken_links),
                    "unchecked_count": max(0, link_total - broken_checked),
                    "examples": [
                        {
                            "url": item.url,
                            "status_code": item.status_code,
                            "error": item.error,
                            "found_on": item.found_on or [],
                        }
                        for item in broken_links[:25]
                    ],
                    "truncated": broken_truncated,
                    "warnings": broken_warnings or [],
                },
                message=f"{len(broken_links)} link target(s) are broken.",
                confidence=_CONFIDENCE_HIGH,
            )
        )
    else:
        checks.append(
            _check(
                "broken_links",
                scope="site",
                status=CheckStatus.passed,
                value={
                    "checked": broken_checked,
                    "broken": 0,
                    "unchecked_count": max(0, link_total - broken_checked),
                    "truncated": broken_truncated,
                    "warnings": broken_warnings or [],
                },
                confidence=_CONFIDENCE_HIGH,
            )
        )

    canonical_groups: dict[str, list[str]] = defaultdict(list)
    for page in pages:
        tree = _tree(page.raw_html)
        hrefs = _canonical_hrefs(tree) if tree is not None else []
        target = urljoin(page.final_url or page.url, hrefs[0]) if hrefs else page.url
        canonical_groups[canonicalize_url(target)].append(page.url)
    duplicate_canonicals = {url: urls for url, urls in canonical_groups.items() if len(urls) > 1}

    title_groups: dict[str, list[str]] = defaultdict(list)
    for page in pages:
        if page.title and page.title.strip():
            title_groups[page.title.strip().lower()].append(page.url)
    duplicate_titles = {title: urls for title, urls in title_groups.items() if len(urls) > 1}

    hash_groups: dict[str, list[str]] = defaultdict(list)
    for page in pages:
        if page.html_sha256:
            hash_groups[page.html_sha256].append(page.url)
    duplicate_hashes = {digest: urls for digest, urls in hash_groups.items() if len(urls) > 1}

    if not pages:
        checks.append(
            _check(
                "duplicates",
                scope="site",
                status=CheckStatus.not_available,
                message="No pages were available for duplicate detection.",
                confidence=_CONFIDENCE_MEDIUM,
            )
        )
    elif duplicate_canonicals or duplicate_titles or duplicate_hashes:
        checks.append(
            _check(
                "duplicates",
                scope="site",
                status=CheckStatus.warning,
                value={
                    "duplicate_canonical_targets": duplicate_canonicals,
                    "duplicate_titles": duplicate_titles,
                    "duplicate_content_hashes": duplicate_hashes,
                },
                message="Duplicate canonical targets, titles, or content hashes were detected.",
                confidence=_CONFIDENCE_MEDIUM,
            )
        )
    else:
        checks.append(
            _check(
                "duplicates",
                scope="site",
                status=CheckStatus.passed,
                value={
                    "duplicate_canonical_targets": {},
                    "duplicate_titles": {},
                    "duplicate_content_hashes": {},
                },
                confidence=_CONFIDENCE_HIGH,
            )
        )

    return checks


def _build_analysis(checks: list[CheckRecord]) -> SeoAnalysis:
    summary = SeoSummary()
    issues: list[SeoIssue] = []
    for check in checks:
        setattr(summary, check.status.value, getattr(summary, check.status.value) + 1)
        if check.status in (CheckStatus.failed, CheckStatus.warning):
            issues.append(
                SeoIssue(
                    id=check.id,
                    url=check.url,
                    message=check.message,
                    confidence=check.confidence,
                )
            )
    return SeoAnalysis(checks=checks, issues=issues, summary=summary)


async def _check_one_link(client, link, found_on: list[str]) -> tuple[BrokenLink | None, str | None]:
    try:
        if link.internal or not hasattr(client, "safe_head"):
            response = await client.safe_get(link.url)
            if link.internal and response.status_code == 405 and hasattr(client, "safe_head"):
                response = await client.safe_head(link.url)
        else:
            response = await client.safe_head(link.url)
            if response.status_code in (403, 405):
                response = await client.safe_get(link.url)
    except Exception as exc:
        return BrokenLink(url=link.url, error=str(exc), found_on=found_on), None
    status = response.status_code
    if status == 429 or (not link.internal and status == 403):
        return None, f"{link.url}: HTTP {status} treated as a warning, not a broken link."
    if status >= 400:
        return BrokenLink(url=link.url, status_code=status, found_on=found_on), None
    return None, None


async def check_broken_links(
    client,
    pages: list[PageData],
    robots=None,
    *,
    max_checks: int = BROKEN_LINK_MAX_CHECKS,
    concurrency: int = BROKEN_LINK_CONCURRENCY,
) -> tuple[list[BrokenLink], int, bool]:
    """Check unique link targets, internal first, bounded by ``max_checks``.

    Returns ``(broken, checked_count, truncated, warnings, total_unique)``.
    """
    unique: dict[str, LinkItem] = {}
    found_on: dict[str, list[str]] = defaultdict(list)
    for page in pages:
        for link in page.links:
            key = canonicalize_url(link.url)
            if key not in unique:
                unique[key] = link
            if page.url not in found_on[key]:
                found_on[key].append(page.url)

    ordered = sorted(unique.values(), key=lambda item: (not item.internal, item.url))
    if max_checks >= 0:
        truncated = len(ordered) > max_checks
        ordered = ordered[:max_checks]
    else:
        truncated = False

    targets = []
    for link in ordered:
        if link.internal and robots is not None and not robots.can_fetch(link.url):
            continue
        targets.append(link)

    semaphore = asyncio.Semaphore(max(1, concurrency))

    async def guarded(link):
        async with semaphore:
            return await _check_one_link(client, link, found_on[canonicalize_url(link.url)])

    results = await asyncio.gather(*(guarded(link) for link in targets))
    broken = [item[0] for item in results if item[0] is not None]
    warnings = [item[1] for item in results if item[1] is not None]
    return broken, len(targets), truncated, warnings, len(unique)


class SeoAnalyzer:
    """Run page-level and site-level SEO checks over crawled pages."""

    async def analyze(
        self,
        pages: list[PageData],
        *,
        robots=None,
        sitemap: SitemapResult | None = None,
        client=None,
        max_broken_links: int = BROKEN_LINK_MAX_CHECKS,
    ) -> ModuleResult[SeoAnalysis]:
        started = time.perf_counter()
        warnings: list[str] = []
        errors: list[ModuleError] = []

        if client is not None and sitemap is None:
            origin = _origin(pages, robots)
            if origin:
                declared = list(getattr(robots, "sitemaps", []) or [])
                sitemap = await fetch_sitemap(client, origin, declared)
                warnings.extend(sitemap.warnings)

        broken_links: list[BrokenLink] | None = None
        broken_checked = 0
        broken_truncated = False
        broken_warnings: list[str] = []
        link_total = 0
        if client is not None:
            (
                broken_links,
                broken_checked,
                broken_truncated,
                broken_warnings,
                link_total,
            ) = await check_broken_links(
                client,
                pages,
                robots,
                max_checks=max_broken_links,
            )
            if broken_truncated:
                warnings.append(f"Broken-link checks were capped at {max_broken_links} targets.")
            warnings.extend(broken_warnings)

        checks: list[CheckRecord] = []
        for page in pages:
            checks.extend(_page_checks(page))
        checks.extend(
            _site_checks(
                pages,
                robots=robots,
                sitemap=sitemap,
                broken_links=broken_links,
                broken_checked=broken_checked,
                broken_truncated=broken_truncated,
                broken_warnings=broken_warnings,
                link_total=link_total,
            )
        )

        analysis = _build_analysis(checks)
        duration_ms = int((time.perf_counter() - started) * 1000)
        if not pages:
            return ModuleResult[SeoAnalysis](
                status=ModuleStatus.partial,
                reason="no_pages",
                duration_ms=duration_ms,
                data=analysis,
                warnings=[*warnings, "No pages were available for page-level SEO checks."],
                errors=errors,
            )
        return ModuleResult[SeoAnalysis](
            status=ModuleStatus.ok,
            duration_ms=duration_ms,
            data=analysis,
            warnings=warnings,
            errors=errors,
        )


async def analyze_seo(
    pages: list[PageData],
    *,
    robots=None,
    sitemap: SitemapResult | None = None,
    client=None,
    max_broken_links: int = BROKEN_LINK_MAX_CHECKS,
) -> ModuleResult[SeoAnalysis]:
    """Convenience wrapper around :class:`SeoAnalyzer`."""
    return await SeoAnalyzer().analyze(
        pages,
        robots=robots,
        sitemap=sitemap,
        client=client,
        max_broken_links=max_broken_links,
    )
