"""Phase 4 tests for the shared browser request guard."""

import pytest

from site_dna.services.browser import BrowserRequestGuard


class FakeRequest:
    def __init__(self, url: str, resource_type: str = "document"):
        self.url = url
        self.resource_type = resource_type


class FakeRoute:
    def __init__(self, url: str, resource_type: str = "document"):
        self.request = FakeRequest(url, resource_type)
        self.aborted: str | None = None
        self.continued = False

    async def abort(self, reason: str = "failed") -> None:
        self.aborted = reason

    async def continue_(self) -> None:
        self.continued = True


async def fake_resolver(host: str) -> list[str]:
    if host in {"127.0.0.1", "169.254.169.254"}:
        return [host]
    return ["93.184.216.34"]


@pytest.mark.anyio
async def test_guard_allows_public_http_requests():
    guard = BrowserRequestGuard(
        allow_private_hosts=False,
        allowed_ports={80, 443},
        resolver=fake_resolver,
    )
    route = FakeRoute("https://example.com/app.js")

    await guard.handle_route(route)

    assert route.continued is True
    assert route.aborted is None
    assert guard.blocked_count == 0


@pytest.mark.anyio
async def test_guard_allows_data_blob_and_about_schemes():
    guard = BrowserRequestGuard(
        allow_private_hosts=False,
        allowed_ports={80, 443},
        resolver=fake_resolver,
    )
    routes = [
        FakeRoute("data:text/css,body%7Bcolor:red%7D"),
        FakeRoute("blob:https://example.com/123"),
        FakeRoute("about:blank"),
    ]

    for route in routes:
        await guard.handle_route(route)
        assert route.continued is True
        assert route.aborted is None

    assert guard.blocked_count == 0


@pytest.mark.anyio
async def test_guard_blocks_private_ip_and_counts_warning():
    guard = BrowserRequestGuard(
        allow_private_hosts=False,
        allowed_ports={80, 443},
        resolver=fake_resolver,
    )
    route = FakeRoute("http://127.0.0.1/secret")

    await guard.handle_route(route)

    assert route.aborted == "blockedbyclient"
    assert route.continued is False
    assert guard.blocked_count == 1
    assert any("blocked" in warning for warning in guard.warnings)


@pytest.mark.anyio
async def test_guard_blocks_metadata_ip():
    guard = BrowserRequestGuard(
        allow_private_hosts=False,
        allowed_ports={80, 443},
        resolver=fake_resolver,
    )
    route = FakeRoute("http://169.254.169.254/latest/meta-data/")

    await guard.handle_route(route)

    assert route.aborted == "blockedbyclient"
    assert guard.blocked_count == 1


@pytest.mark.anyio
async def test_guard_blocks_disallowed_port_scheme_and_credentials():
    guard = BrowserRequestGuard(
        allow_private_hosts=False,
        allowed_ports={80, 443},
        resolver=fake_resolver,
    )
    routes = [
        FakeRoute("https://example.com:8080/app.js"),
        FakeRoute("wss://example.com/socket"),
        FakeRoute("https://user:pass@example.com/app.js"),
        FakeRoute("https://localhost/app.js"),
    ]

    for route in routes:
        await guard.handle_route(route)
        assert route.aborted == "blockedbyclient"
        assert route.continued is False

    assert guard.blocked_count == len(routes)


@pytest.mark.anyio
async def test_guard_blocks_websocket_resource_type():
    guard = BrowserRequestGuard(
        allow_private_hosts=False,
        allowed_ports={80, 443},
        resolver=fake_resolver,
    )
    route = FakeRoute("https://example.com/socket", resource_type="websocket")

    await guard.handle_route(route)

    assert route.aborted == "blockedbyclient"
    assert guard.blocked_count == 1


@pytest.mark.anyio
async def test_guard_allows_loopback_when_private_hosts_enabled():
    guard = BrowserRequestGuard(
        allow_private_hosts=True,
        allowed_ports={80, 443, 8765},
        resolver=fake_resolver,
    )
    route = FakeRoute("http://127.0.0.1:8765/palette.html")

    await guard.handle_route(route)

    assert route.continued is True
    assert route.aborted is None
    assert guard.blocked_count == 0
