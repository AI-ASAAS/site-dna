"""Phase 2 unit tests for the bounded BFS crawl manager."""

import time

import httpx
import pytest

from site_dna.crawler.crawl_manager import CrawlManager, DiscoveredStatus, canonicalize_url
from site_dna.services.http_client import SafeHttpClient
from site_dna.services.security import UrlRejected, ValidatedUrl

ORIGIN = "https://example.com"


async def _validator(url: str) -> ValidatedUrl:
    parts = httpx.URL(url)
    if parts.host in {"127.0.0.1", "localhost"}:
        raise UrlRejected("forbidden_ip", f"blocked {url}")
    return ValidatedUrl(
        url=url,
        scheme=parts.scheme,
        host=parts.host,
        port=parts.port or 443,
        ips=["93.184.216.34"],
    )


def _client(handler) -> SafeHttpClient:
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False)
    return SafeHttpClient(client=http, validator=_validator, per_host_rps=10000, retry_wait=0)


def _manager(client, **kwargs) -> CrawlManager:
    options = {"client": client, "validator": _validator, "max_pages": 10, "max_depth": 2}
    options.update(kwargs)
    return CrawlManager(**options)


def _html(title: str, body: str = "") -> httpx.Response:
    return httpx.Response(
        200,
        text=f"<html><head><title>{title}</title></head><body>{body}</body></html>",
        headers={"Content-Type": "text/html; charset=utf-8"},
    )


def _robots(body: str = "User-agent: *\nAllow: /\n") -> httpx.Response:
    return httpx.Response(200, text=body, headers={"Content-Type": "text/plain"})


@pytest.mark.anyio
async def test_crawl_respects_max_pages_on_large_site():
    log: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        log.append(url)
        if url == f"{ORIGIN}/robots.txt":
            return _robots()
        if url == f"{ORIGIN}/":
            links = "".join(f'<a href="/page/{i}">page {i}</a>' for i in range(100))
            return _html("Home", links)
        if url.startswith(f"{ORIGIN}/page/"):
            return _html(f"Page {url.rsplit('/', 1)[-1]}", '<a href="/page/next">next</a>')
        return httpx.Response(404)

    async with _client(handler) as client:
        manager = _manager(client)
        discovered = await manager.crawl(f"{ORIGIN}/")

    fetched = [item for item in discovered if item.status == DiscoveredStatus.fetched]
    assert len(fetched) <= 10
    assert max(item.depth for item in fetched) <= 2


@pytest.mark.anyio
async def test_crawl_never_fetches_beyond_max_depth():
    log: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        log.append(url)
        if url == f"{ORIGIN}/robots.txt":
            return _robots()
        if url == f"{ORIGIN}/":
            return _html("Home", "".join(f'<a href="/page/{i}">p{i}</a>' for i in range(3)))
        if url.startswith(f"{ORIGIN}/page/"):
            i = url.rsplit("/", 1)[-1]
            return _html(f"Page {i}", f'<a href="/deep/{i}">deep</a>')
        if url.startswith(f"{ORIGIN}/deep/"):
            i = url.rsplit("/", 1)[-1]
            return _html(f"Deep {i}", f'<a href="/too-deep/{i}">too deep</a>')
        if url.startswith(f"{ORIGIN}/too-deep/"):
            return _html("Should never be fetched")
        return httpx.Response(404)

    async with _client(handler) as client:
        manager = _manager(client, max_pages=50)
        discovered = await manager.crawl(f"{ORIGIN}/")

    fetched = [item for item in discovered if item.status == DiscoveredStatus.fetched]
    assert any(item.depth == 2 for item in fetched)
    assert all(item.depth <= 2 for item in fetched)
    assert not any("/too-deep/" in url for url in log)


@pytest.mark.anyio
async def test_crawl_does_not_fetch_robots_disallowed_path():
    log: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        log.append(url)
        if url == f"{ORIGIN}/robots.txt":
            return _robots("User-agent: *\nDisallow: /private/\n")
        if url == f"{ORIGIN}/":
            return _html("Home", '<a href="/private/secret">secret</a><a href="/public">public</a>')
        if url == f"{ORIGIN}/public":
            return _html("Public")
        return httpx.Response(404)

    async with _client(handler) as client:
        manager = _manager(client)
        discovered = await manager.crawl(f"{ORIGIN}/")

    assert not any("/private/secret" in url for url in log)
    private = next(item for item in discovered if item.url.endswith("/private/secret"))
    assert private.status == DiscoveredStatus.skipped_robots


@pytest.mark.anyio
async def test_crawl_never_fetches_off_domain_links():
    log: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        log.append(url)
        if url == f"{ORIGIN}/robots.txt":
            return _robots()
        if url == f"{ORIGIN}/":
            return _html("Home", '<a href="https://external.org/page">external</a>')
        return httpx.Response(404)

    async with _client(handler) as client:
        manager = _manager(client)
        discovered = await manager.crawl(f"{ORIGIN}/")

    assert not any("external.org" in url for url in log)
    external = next(item for item in discovered if "external.org" in item.url)
    assert external.status == DiscoveredStatus.skipped_scope


@pytest.mark.anyio
async def test_crawl_skips_non_html_extensions():
    log: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        log.append(url)
        if url == f"{ORIGIN}/robots.txt":
            return _robots()
        if url == f"{ORIGIN}/":
            return _html("Home", '<a href="/brochure.pdf">pdf</a>')
        return httpx.Response(404)

    async with _client(handler) as client:
        manager = _manager(client)
        discovered = await manager.crawl(f"{ORIGIN}/")

    assert not any("brochure.pdf" in url for url in log)
    pdf = next(item for item in discovered if item.url.endswith("/brochure.pdf"))
    assert pdf.status == DiscoveredStatus.skipped_scope


@pytest.mark.anyio
async def test_crawl_canonicalizes_and_deduplicates_urls():
    log: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        log.append(url)
        if url == f"{ORIGIN}/robots.txt":
            return _robots()
        if url == f"{ORIGIN}/":
            return _html(
                "Home",
                '<a href="/about/?utm_source=x&b=2&a=1#team">one</a>'
                '<a href="/about?a=1&b=2">two</a>'
                '<a href="/services/">three</a>',
            )
        if url == f"{ORIGIN}/about?a=1&b=2":
            return _html("About")
        if url == f"{ORIGIN}/services":
            return _html("Services")
        return httpx.Response(404)

    async with _client(handler) as client:
        manager = _manager(client)
        await manager.crawl(f"{ORIGIN}/")

    about_requests = [url for url in log if "/about" in url]
    assert about_requests == [f"{ORIGIN}/about?a=1&b=2"]
    assert f"{ORIGIN}/services" in log


@pytest.mark.anyio
async def test_crawl_enforces_wall_clock_budget():
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url == f"{ORIGIN}/robots.txt":
            return _robots()
        if url == f"{ORIGIN}/":
            return _html("Home", "".join(f'<a href="/page/{i}">p{i}</a>' for i in range(50)))
        time.sleep(0.02)
        return _html("Page")

    async with _client(handler) as client:
        manager = _manager(client, max_pages=50, max_total_seconds=0.01)
        started = time.monotonic()
        discovered = await manager.crawl(f"{ORIGIN}/")
        elapsed = time.monotonic() - started

    assert elapsed < 1.0
    assert any(item.status == DiscoveredStatus.skipped_limit for item in discovered)


@pytest.mark.anyio
async def test_crawl_assigns_categories():
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url == f"{ORIGIN}/robots.txt":
            return _robots()
        if url == f"{ORIGIN}/":
            return _html("Home", '<a href="/about">about</a><a href="/pricing">pricing</a>')
        if url == f"{ORIGIN}/about":
            return _html("About Us")
        if url == f"{ORIGIN}/pricing":
            return _html("Pricing")
        return httpx.Response(404)

    async with _client(handler) as client:
        manager = _manager(client)
        discovered = await manager.crawl(f"{ORIGIN}/")

    by_url = {item.url: item for item in discovered}
    assert by_url[f"{ORIGIN}/"].category == "home"
    assert by_url[f"{ORIGIN}/about"].category == "about"
    assert by_url[f"{ORIGIN}/pricing"].category == "pricing"


def test_canonicalize_url_strips_tracking_sorts_query_and_trailing_slash():
    assert (
        canonicalize_url("https://example.com/about/?utm_source=x&b=2&a=1#team")
        == "https://example.com/about?a=1&b=2"
    )
    assert canonicalize_url("https://example.com/") == "https://example.com/"
