"""Crawl4AI-backed content extraction for each crawled URL (Phase 3)."""

import hashlib
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol, Sequence
from urllib.parse import urljoin, urlsplit

os.environ.setdefault("CRAWL4AI_NO_CLOUD_NOTICE", "1")

from crawl4ai import (  # noqa: E402
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
)
from crawl4ai.content_filter_strategy import PruningContentFilterLXML  # noqa: E402
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator  # noqa: E402
from selectolax.lexbor import LexborHTMLParser  # noqa: E402

from site_dna.analyzers.noise import EXCLUDED_SELECTOR, EXCLUDED_SELECTORS, EXCLUDED_TAGS
from site_dna.core.logging import get_logger
from site_dna.crawler.crawl_manager import DiscoveredUrl
from site_dna.models.common import FileRef, ModuleError, ModuleResult, ModuleStatus
from site_dna.models.page import (
    HeadingLists,
    HeadingOutlineItem,
    ImageItem,
    LinkItem,
    PageData,
)
from site_dna.models.report import WebsiteContent
from site_dna.services.normalizer import registrable_domain, strip_fragment

logger = get_logger("analyzers.content_extractor")

NON_HTTP_SCHEMES = frozenset({"mailto", "tel", "javascript", "data", "blob"})


@dataclass(slots=True)
class RenderedPage:
    """Rendered HTML and Markdown returned for one URL."""

    url: str
    final_url: str | None = None
    status_code: int | None = None
    html: str = ""
    raw_markdown: str = ""
    fit_markdown: str | None = None
    fetch_ms: int | None = None


class PageRenderer(Protocol):
    """Minimal renderer contract used by the extractor and its tests."""

    async def __aenter__(self) -> "PageRenderer":
        ...

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        ...

    async def render(self, url: str) -> RenderedPage:
        ...


class Crawl4AIRenderer:
    """Render pages with Crawl4AI using the locally installed Chromium."""

    def __init__(
        self,
        *,
        browser_config: BrowserConfig | None = None,
        run_config: CrawlerRunConfig | None = None,
        page_timeout_ms: int = 30_000,
    ) -> None:
        self._browser_config = browser_config or BrowserConfig(headless=True, verbose=False)
        self._run_config = run_config or CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilterLXML()
            ),
            excluded_tags=list(EXCLUDED_TAGS),
            excluded_selector=EXCLUDED_SELECTOR,
            remove_forms=True,
            check_robots_txt=False,
            page_timeout=page_timeout_ms,
        )
        self._crawler: AsyncWebCrawler | None = None

    async def __aenter__(self) -> "Crawl4AIRenderer":
        crawler = AsyncWebCrawler(config=self._browser_config)
        await crawler.__aenter__()
        self._crawler = crawler
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._crawler is not None:
            await self._crawler.__aexit__(exc_type, exc_val, exc_tb)
            self._crawler = None
        return None

    async def render(self, url: str) -> RenderedPage:
        if self._crawler is None:
            raise RuntimeError("Crawl4AIRenderer must be used as an async context manager")

        started = time.perf_counter()
        result = await self._crawler.arun(url=url, config=self._run_config)
        fetch_ms = int((time.perf_counter() - started) * 1000)

        if isinstance(result, list):
            if not result:
                raise RuntimeError("Crawl4AI returned no results")
            result = result[0]

        markdown = getattr(result, "markdown", None)
        if isinstance(markdown, str):
            raw_markdown = markdown
            fit_markdown = markdown
        else:
            raw_markdown = getattr(markdown, "raw_markdown", "") or ""
            fit_markdown = getattr(markdown, "fit_markdown", None)

        html = getattr(result, "html", "") or ""
        status_code = getattr(result, "status_code", None)
        final_url = getattr(result, "redirected_url", None) or getattr(result, "url", None) or url

        if not html and not raw_markdown and not fit_markdown:
            if status_code is None or status_code < 400:
                message = getattr(result, "error_message", None) or (
                    "render produced no HTML or Markdown"
                )
                raise RuntimeError(message)

        return RenderedPage(
            url=url,
            final_url=final_url,
            status_code=status_code,
            html=html,
            raw_markdown=raw_markdown,
            fit_markdown=fit_markdown,
            fetch_ms=fetch_ms,
        )


class ContentExtractor:
    """Extract structured page content for every crawled URL."""

    def __init__(
        self,
        *,
        scan_id: str,
        storage_dir: str | Path,
        renderer: PageRenderer | None = None,
        inline_markdown_limit: int = 100_000,
    ) -> None:
        self._scan_id = scan_id
        self._storage_dir = Path(storage_dir)
        self._renderer = renderer
        self._inline_markdown_limit = inline_markdown_limit

    async def extract(
        self, targets: Sequence[DiscoveredUrl]
    ) -> ModuleResult[WebsiteContent]:
        started = time.perf_counter()
        target_list = list(targets)

        if not target_list:
            return ModuleResult[WebsiteContent](
                status=ModuleStatus.skipped,
                reason="no crawled URLs",
                duration_ms=_elapsed_ms(started),
                data=WebsiteContent(),
            )

        pages: list[PageData] = []
        warnings: list[str] = []
        errors: list[ModuleError] = []
        renderer = self._renderer or Crawl4AIRenderer()

        async with renderer:
            for index, target in enumerate(target_list, start=1):
                try:
                    rendered = await renderer.render(target.url)
                    page = self._build_page(target, rendered, index, warnings)
                except Exception as exc:  # noqa: BLE001 - one page must not abort the module
                    logger.warning("page extraction failed", extra={"url": target.url})
                    page = self._error_page(target, exc)

                if page.error:
                    errors.append(
                        ModuleError(code="page_failed", message=page.error, url=page.url)
                    )
                pages.append(page)

        pages_failed = sum(1 for page in pages if page.error)
        total_words = sum(page.word_count or 0 for page in pages)
        data = WebsiteContent(
            pages=pages,
            total_pages=len(pages),
            total_words=total_words,
            pages_failed=pages_failed,
        )

        status = _module_status(pages, pages_failed)
        reason = None
        if status is ModuleStatus.failed:
            reason = "start URL could not be extracted"
        elif status is ModuleStatus.partial:
            reason = f"{pages_failed} page(s) failed"

        return ModuleResult[WebsiteContent](
            status=status,
            reason=reason,
            duration_ms=_elapsed_ms(started),
            data=data,
            warnings=warnings,
            errors=errors,
        )

    def _build_page(
        self,
        target: DiscoveredUrl,
        rendered: RenderedPage,
        index: int,
        warnings: list[str],
    ) -> PageData:
        final_url = rendered.final_url or target.url
        tree = _clean_tree(rendered.html)

        h1 = _heading_texts(tree, "h1")
        h2 = _heading_texts(tree, "h2")
        h3 = _heading_texts(tree, "h3")
        outline = [
            HeadingOutlineItem(level=int(node.tag[1]), text=node.text(strip=True))
            for node in tree.css("h1, h2, h3")
            if node.text(strip=True)
        ]

        links, non_http_counts = _extract_links(tree, final_url)
        markdown, markdown_file, markdown_chars = self._store_markdown(
            rendered, target.url, index, warnings
        )
        html = rendered.html or ""

        page = PageData(
            url=target.url,
            final_url=final_url,
            http_status=rendered.status_code,
            category=target.category,
            depth=target.depth,
            fetched_at=datetime.now(timezone.utc),
            fetch_ms=rendered.fetch_ms,
            title=_first_text(tree, "title"),
            language=_language(tree),
            markdown=markdown,
            markdown_file=markdown_file,
            markdown_chars=markdown_chars,
            word_count=len(markdown.split()) if markdown else 0,
            headings=HeadingLists(h1=h1, h2=h2, h3=h3),
            heading_outline=outline,
            paragraphs_count=len(tree.css("p")),
            lists_count=len(tree.css("ul")) + len(tree.css("ol")),
            links=links,
            images=_extract_images(tree, final_url),
            html_sha256=hashlib.sha256(html.encode("utf-8")).hexdigest() if html else None,
            raw_html=html or None,
            non_http_link_counts=non_http_counts,
        )

        if rendered.status_code is None:
            page.error = "no HTTP status"
        elif rendered.status_code >= 400:
            page.error = f"HTTP {rendered.status_code}"

        return page

    def _store_markdown(
        self,
        rendered: RenderedPage,
        url: str,
        index: int,
        warnings: list[str],
    ) -> tuple[str | None, FileRef | None, int]:
        raw_markdown = rendered.raw_markdown or ""
        fit_markdown = rendered.fit_markdown or ""

        if fit_markdown:
            markdown: str | None = fit_markdown
        elif raw_markdown:
            markdown = raw_markdown
            warnings.append(
                f"{url}: fit markdown empty; using raw markdown "
                f"(raw={len(raw_markdown)} chars, fit=0)"
            )
        else:
            return None, None, 0

        markdown_chars = len(markdown)
        if markdown_chars <= self._inline_markdown_limit:
            return markdown, None, markdown_chars

        encoded = markdown.encode("utf-8")
        pages_dir = self._storage_dir / self._scan_id / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)
        path = pages_dir / f"{index}.md"
        path.write_text(markdown, encoding="utf-8")
        file_ref = FileRef(
            path=str(path),
            format="markdown",
            bytes=len(encoded),
            sha256=hashlib.sha256(encoded).hexdigest(),
        )
        return None, file_ref, markdown_chars

    @staticmethod
    def _error_page(target: DiscoveredUrl, exc: Exception) -> PageData:
        return PageData(
            url=target.url,
            final_url=target.url,
            category=target.category,
            depth=target.depth,
            fetched_at=datetime.now(timezone.utc),
            error=str(exc) or exc.__class__.__name__,
        )


def _clean_tree(html: str) -> LexborHTMLParser:
    tree = LexborHTMLParser(html or "")
    for tag in EXCLUDED_TAGS:
        for node in tree.css(tag):
            node.decompose()
    for selector in EXCLUDED_SELECTORS:
        for node in tree.css(selector):
            node.decompose()
    return tree


def _heading_texts(tree: LexborHTMLParser, tag: str) -> list[str]:
    return [text for node in tree.css(tag) if (text := node.text(strip=True))]


def _first_text(tree: LexborHTMLParser, selector: str) -> str | None:
    node = tree.css_first(selector)
    if node is None:
        return None
    text = node.text(strip=True)
    return text or None


def _language(tree: LexborHTMLParser) -> str | None:
    node = tree.css_first("html")
    if node is None:
        return None
    return node.attributes.get("lang") or None


def _extract_links(
    tree: LexborHTMLParser, final_url: str
) -> tuple[list[LinkItem], dict[str, int]]:
    base_host = urlsplit(final_url).hostname or ""
    base_domain = registrable_domain(base_host)
    non_http_counts: dict[str, int] = {}
    links: list[LinkItem] = []
    seen: set[str] = set()

    for node in tree.css("a[href]"):
        href = (node.attributes.get("href") or "").strip()
        if not href:
            continue

        scheme = href.split(":", 1)[0].lower() if ":" in href else ""
        if scheme in NON_HTTP_SCHEMES:
            non_http_counts[scheme] = non_http_counts.get(scheme, 0) + 1
            continue

        absolute = strip_fragment(urljoin(final_url, href))
        if absolute in seen:
            continue
        seen.add(absolute)

        host = urlsplit(absolute).hostname or ""
        internal = bool(host and base_domain and registrable_domain(host) == base_domain)
        links.append(
            LinkItem(
                url=absolute,
                text=node.text(strip=True) or "",
                internal=internal,
                rel=node.attributes.get("rel"),
            )
        )

    return links, non_http_counts


def _extract_images(tree: LexborHTMLParser, final_url: str) -> list[ImageItem]:
    images: list[ImageItem] = []
    for node in tree.css("img"):
        attributes = node.attributes
        src = attributes.get("src") or attributes.get("data-src")
        if not src:
            srcset = attributes.get("srcset") or ""
            first_candidate = srcset.split(",", 1)[0].strip()
            src = first_candidate.split(" ", 1)[0] if first_candidate else ""
        if not src:
            continue

        images.append(
            ImageItem(
                src=urljoin(final_url, src.strip()),
                alt=attributes.get("alt"),
                width=_int_or_none(attributes.get("width")),
                height=_int_or_none(attributes.get("height")),
                loading=attributes.get("loading"),
            )
        )
    return images


def _int_or_none(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _module_status(pages: list[PageData], pages_failed: int) -> ModuleStatus:
    if pages_failed == 0:
        return ModuleStatus.ok
    if pages and pages[0].error:
        return ModuleStatus.failed
    return ModuleStatus.partial


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)
