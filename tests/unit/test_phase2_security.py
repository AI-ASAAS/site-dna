"""Phase 2 unit tests for URL validation and SSRF-safe IP policy."""

import ipaddress

import pytest

from site_dna.services.security import (
    UrlRejected,
    ValidatedUrl,
    is_ip_allowed,
    validate_url,
)


@pytest.mark.parametrize(
    "ip",
    [
        "8.8.8.8",
        "1.1.1.1",
        "2606:4700:4700::1111",
    ],
)
def test_is_ip_allowed_accepts_public_addresses(ip):
    assert is_ip_allowed(ip) is True


@pytest.mark.parametrize(
    "ip",
    [
        "127.0.0.1",
        "::1",
        "10.0.0.1",
        "172.16.5.4",
        "192.168.1.10",
        "169.254.169.254",
        "169.254.1.1",
        "fe80::1",
        "224.0.0.1",
        "0.0.0.0",
        "100.64.0.1",
        "100.100.100.200",
        "::ffff:127.0.0.1",
        "::ffff:169.254.169.254",
    ],
)
def test_is_ip_allowed_rejects_non_public_addresses(ip):
    assert is_ip_allowed(ip) is False


def test_is_ip_allowed_rejects_invalid_literals():
    assert is_ip_allowed("not-an-ip") is False


def test_is_ip_allowed_accepts_ipaddress_objects():
    assert is_ip_allowed(ipaddress.ip_address("8.8.8.8")) is True
    assert is_ip_allowed(ipaddress.ip_address("127.0.0.1")) is False


@pytest.mark.anyio
@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com/file.txt",
        "gopher://example.com/",
    ],
)
async def test_validate_url_rejects_disallowed_schemes(url):
    with pytest.raises(UrlRejected) as exc:
        await validate_url(url)
    assert exc.value.code == "invalid_scheme"


@pytest.mark.anyio
async def test_validate_url_rejects_credentials():
    with pytest.raises(UrlRejected) as exc:
        await validate_url("https://user:pass@example.com/")
    assert exc.value.code == "credentials_not_allowed"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://[::1]/",
        "http://10.0.0.1/",
        "http://169.254.169.254/latest/meta-data/",
        "http://localhost/",
        "http://server.internal/",
        "http://printer.local/",
    ],
)
async def test_validate_url_rejects_private_targets(url):
    with pytest.raises(UrlRejected):
        await validate_url(url)


@pytest.mark.anyio
async def test_validate_url_returns_validated_url_for_public_host():
    async def resolver(host: str) -> list[str]:
        assert host == "example.com"
        return ["93.184.216.34", "2606:2800:220:1:248:1893:25c8:1946"]

    result = await validate_url("HTTPS://Example.COM:443/about#team", resolver=resolver)

    assert isinstance(result, ValidatedUrl)
    assert result.url == "https://example.com/about"
    assert result.scheme == "https"
    assert result.host == "example.com"
    assert result.port == 443
    assert result.ips == ["93.184.216.34", "2606:2800:220:1:248:1893:25c8:1946"]


@pytest.mark.anyio
async def test_validate_url_idna_encodes_host():
    async def resolver(host: str) -> list[str]:
        return ["93.184.216.34"]

    result = await validate_url("https://münich.example/", resolver=resolver)
    assert result.host == "xn--mnich-kva.example"


@pytest.mark.anyio
async def test_validate_url_rejects_when_any_resolved_ip_is_private():
    async def resolver(host: str) -> list[str]:
        return ["93.184.216.34", "10.0.0.5"]

    with pytest.raises(UrlRejected) as exc:
        await validate_url("https://example.com/", resolver=resolver)
    assert exc.value.code == "forbidden_ip"


@pytest.mark.anyio
async def test_validate_url_rejects_non_standard_port():
    with pytest.raises(UrlRejected) as exc:
        await validate_url("https://example.com:8443/")
    assert exc.value.code == "port_not_allowed"


@pytest.mark.anyio
async def test_validate_url_allows_configured_extra_port():
    async def resolver(host: str) -> list[str]:
        return ["93.184.216.34"]

    result = await validate_url(
        "https://example.com:8443/",
        allowed_ports={80, 443, 8443},
        resolver=resolver,
    )
    assert result.port == 8443


@pytest.mark.anyio
async def test_validate_url_defaults_missing_scheme_to_https():
    async def resolver(host: str) -> list[str]:
        return ["93.184.216.34"]

    result = await validate_url("example.com", resolver=resolver)
    assert result.url == "https://example.com/"


@pytest.mark.anyio
async def test_validate_url_honors_private_hosts_only_when_explicitly_enabled():
    async def resolver(host: str) -> list[str]:
        return ["127.0.0.1"]

    with pytest.raises(UrlRejected):
        await validate_url("http://127.0.0.1/", resolver=resolver)

    result = await validate_url("http://127.0.0.1/", allow_private_hosts=True, resolver=resolver)
    assert result.host == "127.0.0.1"
    assert result.ips == ["127.0.0.1"]


@pytest.mark.anyio
async def test_validate_url_rejects_empty_input():
    with pytest.raises(UrlRejected) as exc:
        await validate_url("   ")
    assert exc.value.code == "empty_url"
