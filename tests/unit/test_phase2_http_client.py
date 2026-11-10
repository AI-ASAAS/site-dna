"""Phase 2 unit tests for the safe HTTP client: redirects, limits, retries, rate limiting."""

import time

import httpx
import pytest

from site_dna.services.http_client import (
    USER_AGENT,
    FetchError,
    ResponseTooLargeError,
    SafeHttpClient,
    TokenBucket,
    create_async_client,
)
from site_dna.services.security import UrlRejected, ValidatedUrl


def _allow_all(url: str) -> ValidatedUrl:
    parts = httpx.URL(url)
    return ValidatedUrl(
        url=url,
        scheme=parts.scheme,
        host=parts.host,
        port=parts.port or (80 if parts.scheme == "http" else 443),
        ips=["93.184.216.34"],
    )


async def _fake_validator(url: str) -> ValidatedUrl:
    if "127.0.0.1" in url or "localhost" in url:
        raise UrlRejected("forbidden_ip", f"blocked {url}")
    return _allow_all(url)


def _client(handler, **kwargs) -> SafeHttpClient:
    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport, follow_redirects=False)
    options = {
        "client": http,
        "validator": _fake_validator,
        "per_host_rps": 10000,
        "retry_wait": 0,
    }
    options.update(kwargs)
    return SafeHttpClient(**options)


@pytest.mark.anyio
async def test_safe_get_follows_redirects_manually():
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        if str(request.url) == "https://example.com/start":
            return httpx.Response(302, headers={"Location": "https://example.com/final"})
        return httpx.Response(200, text="ok", headers={"Content-Type": "text/html"})

    async with _client(handler) as client:
        response = await client.safe_get("https://example.com/start")

    assert response.status_code == 200
    assert response.final_url == "https://example.com/final"
    assert response.text == "ok"
    assert response.redirect_history == ["https://example.com/start"]
    assert requests == ["https://example.com/start", "https://example.com/final"]


@pytest.mark.anyio
async def test_safe_get_validates_every_redirect_hop():
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        return httpx.Response(302, headers={"Location": "http://127.0.0.1/secret"})

    async with _client(handler) as client:
        with pytest.raises(UrlRejected):
            await client.safe_get("https://example.com/start")

    assert requests == ["https://example.com/start"]


@pytest.mark.anyio
async def test_safe_get_stops_after_max_redirects():
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        return httpx.Response(302, headers={"Location": f"https://example.com/hop{len(requests)}"})

    async with _client(handler, max_redirects=5) as client:
        with pytest.raises(FetchError):
            await client.safe_get("https://example.com/start")

    assert len(requests) == 6


@pytest.mark.anyio
async def test_safe_get_enforces_max_body_size():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"x" * 200, headers={"Content-Type": "text/html"})

    async with _client(handler, max_bytes=100) as client:
        with pytest.raises(ResponseTooLargeError):
            await client.safe_get("https://example.com/big")


@pytest.mark.anyio
async def test_safe_get_retries_5xx_then_succeeds():
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] < 3:
            return httpx.Response(503, text="unavailable")
        return httpx.Response(200, text="ok", headers={"Content-Type": "text/html"})

    async with _client(handler, retries=2) as client:
        response = await client.safe_get("https://example.com/flaky")

    assert response.status_code == 200
    assert attempts["count"] == 3


@pytest.mark.anyio
async def test_safe_get_does_not_retry_4xx():
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        return httpx.Response(404, text="missing")

    async with _client(handler, retries=2) as client:
        response = await client.safe_get("https://example.com/missing")

    assert response.status_code == 404
    assert attempts["count"] == 1


@pytest.mark.anyio
async def test_safe_get_retries_timeouts():
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise httpx.ConnectTimeout("boom")
        return httpx.Response(200, text="ok", headers={"Content-Type": "text/html"})

    async with _client(handler, retries=2) as client:
        response = await client.safe_get("https://example.com/slow")

    assert response.status_code == 200
    assert attempts["count"] == 3


@pytest.mark.anyio
async def test_safe_get_raises_fetch_error_after_timeout_retries():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("boom")

    async with _client(handler, retries=2) as client:
        with pytest.raises(FetchError):
            await client.safe_get("https://example.com/slow")


@pytest.mark.anyio
async def test_safe_head_uses_head_method_and_returns_no_body():
    seen_methods: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_methods.append(request.method)
        return httpx.Response(200, headers={"Content-Type": "text/html", "X-Test": "yes"})

    async with _client(handler) as client:
        response = await client.safe_head("https://example.com/")

    assert seen_methods == ["HEAD"]
    assert response.status_code == 200
    assert response.content == b""
    assert response.headers["x-test"] == "yes"


@pytest.mark.anyio
async def test_token_bucket_waits_between_requests():
    bucket = TokenBucket(rate=20.0)
    await bucket.acquire()

    started = time.perf_counter()
    await bucket.acquire()
    elapsed = time.perf_counter() - started

    assert elapsed >= 0.04


@pytest.mark.anyio
async def test_create_async_client_uses_identifying_user_agent_and_no_auto_redirects():
    client = create_async_client()
    try:
        assert client.headers["user-agent"] == USER_AGENT
        assert client.follow_redirects is False
    finally:
        await client.aclose()
