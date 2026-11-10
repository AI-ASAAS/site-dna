"""Phase 2 unit tests for robots.txt fetching and policy exposure."""

import httpx
import pytest

from site_dna.crawler.robots import RobotsStatus, RobotsTxt, fetch_robots
from site_dna.services.http_client import SafeHttpClient
from site_dna.services.security import ValidatedUrl

ORIGIN = "https://example.com"


def _validator(url: str) -> ValidatedUrl:
    parts = httpx.URL(url)
    return ValidatedUrl(
        url=url,
        scheme=parts.scheme,
        host=parts.host,
        port=parts.port or 443,
        ips=["93.184.216.34"],
    )


async def _fake_validator(url: str) -> ValidatedUrl:
    return _validator(url)


def _client(handler) -> SafeHttpClient:
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False)
    return SafeHttpClient(client=http, validator=_fake_validator, per_host_rps=10000, retry_wait=0)


@pytest.mark.anyio
async def test_fetch_robots_parses_rules_delay_and_sitemaps():
    body = (
        "User-agent: *\n"
        "Disallow: /private/\n"
        "Crawl-delay: 5\n"
        "Sitemap: https://example.com/sitemap.xml\n"
        "Sitemap: https://example.com/news-sitemap.xml\n"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == f"{ORIGIN}/robots.txt"
        return httpx.Response(200, text=body, headers={"Content-Type": "text/plain"})

    async with _client(handler) as client:
        robots = await fetch_robots(client, ORIGIN)

    assert isinstance(robots, RobotsTxt)
    assert robots.status == RobotsStatus.found
    assert robots.can_fetch(f"{ORIGIN}/private/secret") is False
    assert robots.can_fetch(f"{ORIGIN}/public") is True
    assert robots.crawl_delay == 5.0
    assert robots.sitemaps == [
        "https://example.com/sitemap.xml",
        "https://example.com/news-sitemap.xml",
    ]


@pytest.mark.anyio
async def test_fetch_robots_blocks_root_when_disallow_root():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="User-agent: *\nDisallow: /\n", headers={"Content-Type": "text/plain"})

    async with _client(handler) as client:
        robots = await fetch_robots(client, ORIGIN)

    assert robots.status == RobotsStatus.found
    assert robots.can_fetch(f"{ORIGIN}/") is False
    assert robots.can_fetch(f"{ORIGIN}/anything") is False


@pytest.mark.anyio
async def test_fetch_robots_missing_means_allow_all():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found")

    async with _client(handler) as client:
        robots = await fetch_robots(client, ORIGIN)

    assert robots.status == RobotsStatus.missing
    assert robots.can_fetch(f"{ORIGIN}/anything") is True
    assert robots.crawl_delay is None
    assert robots.sitemaps == []


@pytest.mark.anyio
async def test_fetch_robots_server_error_is_error_but_allows_with_warning():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="unavailable")

    async with _client(handler) as client:
        robots = await fetch_robots(client, ORIGIN)

    assert robots.status == RobotsStatus.error
    assert robots.can_fetch(f"{ORIGIN}/anything") is True
    assert robots.warning is not None


@pytest.mark.anyio
async def test_fetch_robots_network_error_is_error_but_allows():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    async with _client(handler) as client:
        robots = await fetch_robots(client, ORIGIN)

    assert robots.status == RobotsStatus.error
    assert robots.can_fetch(f"{ORIGIN}/anything") is True


def test_robots_txt_without_crawl_delay_returns_none():
    robots = RobotsTxt.from_text(ORIGIN, "User-agent: *\nAllow: /\n")
    assert robots.status == RobotsStatus.found
    assert robots.crawl_delay is None
