"""Security tests for BrowserSecurityPolicy: egress filtering, SSRF prevention, scheme control."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from site_dna.visual.browser_security import BrowserSecurityPolicy


def _make_mock_route(url: str, resource_type: str = "document") -> MagicMock:
    route = MagicMock()
    route.abort = AsyncMock()
    route.continue_ = AsyncMock()
    request = MagicMock()
    request.url = url
    request.resource_type = resource_type
    route.request = request
    return route


@pytest.mark.asyncio
async def test_policy_blocks_websockets():
    policy = BrowserSecurityPolicy(allowed_origin="https://example.com")
    route = _make_mock_route("wss://example.com/socket", resource_type="websocket")

    await policy.handle_route(route)
    route.abort.assert_awaited_once_with("blockedbyclient")
    route.continue_.assert_not_awaited()


@pytest.mark.asyncio
async def test_policy_blocks_disallowed_schemes():
    policy = BrowserSecurityPolicy(allowed_origin="https://example.com")

    for bad_url in [
        "file:///C:/Windows/win.ini",
        "file:///etc/passwd",
        "ftp://ftp.example.com/file.txt",
        "javascript:alert(1)",
        "gopher://example.com",
    ]:
        route = _make_mock_route(bad_url)
        await policy.handle_route(route)
        route.abort.assert_awaited_once_with("accessdenied")
        route.continue_.assert_not_awaited()


@pytest.mark.asyncio
async def test_policy_allows_safe_non_network_schemes():
    policy = BrowserSecurityPolicy(allowed_origin="https://example.com")

    for safe_url in [
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "about:blank",
        "blob:https://example.com/some-uuid",
    ]:
        route = _make_mock_route(safe_url, resource_type="image")
        await policy.handle_route(route)
        route.continue_.assert_awaited_once()
        route.abort.assert_not_awaited()


@pytest.mark.asyncio
async def test_policy_blocks_cloud_metadata():
    policy = BrowserSecurityPolicy(allowed_origin="https://example.com")

    # AWS/GCP/Azure instance metadata
    metadata_urls = [
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://169.254.169.254/metadata/v1/maintenance",
    ]

    for url in metadata_urls:
        route = _make_mock_route(url)
        await policy.handle_route(route)
        route.abort.assert_awaited_once_with("accessdenied")
        route.continue_.assert_not_awaited()


@pytest.mark.asyncio
async def test_policy_blocks_private_ips_and_loopback():
    policy = BrowserSecurityPolicy(allowed_origin="https://example.com")

    forbidden_urls = [
        "http://127.0.0.1:8000/api",
        "http://localhost:3000/",
        "http://10.0.0.1/admin",
        "http://192.168.1.1/router",
        "http://172.16.0.1/internal",
        "http://0.0.0.0/",
    ]

    for url in forbidden_urls:
        route = _make_mock_route(url)
        await policy.handle_route(route)
        route.abort.assert_awaited_once_with("accessdenied")
        route.continue_.assert_not_awaited()


@pytest.mark.asyncio
async def test_policy_allows_test_loopback_when_explicitly_configured():
    policy = BrowserSecurityPolicy(
        allowed_origin="http://127.0.0.1:8080",
        allow_test_loopback=True,
        test_fixture_origin="http://127.0.0.1:8080",
    )

    route = _make_mock_route("http://127.0.0.1:8080/index.html")
    await policy.handle_route(route)
    route.continue_.assert_awaited_once()
    route.abort.assert_not_awaited()
