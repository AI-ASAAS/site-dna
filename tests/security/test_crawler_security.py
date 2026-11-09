"""Security unit and integration tests verifying SSRF protection, XXE defense, and limits."""

import ipaddress

import pytest

from site_dna.core.security import (
    SecurityValidationError,
    is_ip_forbidden,
    resolve_and_validate_host,
)
from site_dna.discovery.http_client import ResponseTooLargeError, SecureHttpClient
from site_dna.discovery.sitemap import _extract_loc_values
from site_dna.discovery.url_validator import normalize_url


def test_ip_forbidden_check():
    # Loopback
    assert is_ip_forbidden(ipaddress.ip_address("127.0.0.1")) is True
    assert is_ip_forbidden(ipaddress.ip_address("::1")) is True

    # Private ranges
    assert is_ip_forbidden(ipaddress.ip_address("10.0.0.1")) is True
    assert is_ip_forbidden(ipaddress.ip_address("172.16.0.1")) is True
    assert is_ip_forbidden(ipaddress.ip_address("192.168.1.1")) is True

    # Cloud metadata
    assert is_ip_forbidden(ipaddress.ip_address("169.254.169.254")) is True
    assert is_ip_forbidden(ipaddress.ip_address("100.100.100.200")) is True

    # Link-local & multicast
    assert is_ip_forbidden(ipaddress.ip_address("169.254.1.1")) is True
    assert is_ip_forbidden(ipaddress.ip_address("224.0.0.1")) is True

    # IPv4-mapped IPv6
    assert is_ip_forbidden(ipaddress.ip_address("::ffff:127.0.0.1")) is True
    assert is_ip_forbidden(ipaddress.ip_address("::ffff:169.254.169.254")) is True
    assert is_ip_forbidden(ipaddress.ip_address("::ffff:10.0.0.1")) is True

    # Public IP
    assert is_ip_forbidden(ipaddress.ip_address("8.8.8.8")) is False
    assert is_ip_forbidden(ipaddress.ip_address("1.1.1.1")) is False


def test_resolve_and_validate_host_blocks_forbidden_names():
    with pytest.raises(SecurityValidationError, match="forbidden"):
        resolve_and_validate_host("localhost")

    with pytest.raises(SecurityValidationError, match="forbidden"):
        resolve_and_validate_host("metadata.google.internal")

    with pytest.raises(SecurityValidationError, match="forbidden"):
        resolve_and_validate_host("server.internal")


def test_resolve_and_validate_host_blocks_raw_private_ips():
    with pytest.raises(SecurityValidationError, match="private, loopback|forbidden"):
        resolve_and_validate_host("127.0.0.1")

    with pytest.raises(SecurityValidationError, match="private, loopback|forbidden"):
        resolve_and_validate_host("192.168.0.1")

    with pytest.raises(SecurityValidationError, match="private, loopback|forbidden"):
        resolve_and_validate_host("169.254.169.254")


def test_normalize_url_ssrf_boundary_cases():
    with pytest.raises(SecurityValidationError):
        normalize_url("file:///etc/shadow")

    with pytest.raises(SecurityValidationError):
        normalize_url("gopher://127.0.0.1:70/_test")

    with pytest.raises(SecurityValidationError):
        normalize_url("http://user:password@target.com/")

    with pytest.raises(SecurityValidationError):
        normalize_url("https://target.com:22/")


def test_defusedxml_blocks_xxe_entity_expansion():
    # Classic XXE payload attempting to expand external entity
    malicious_xml = (
        b'<?xml version="1.0" encoding="ISO-8859-1"?>'
        b"<!DOCTYPE foo ["
        b"  <!ELEMENT foo ANY >"
        b'  <!ENTITY xxe SYSTEM "file:///etc/passwd" >]><foo>&xxe;</foo>'
    )

    # defusedxml should either raise DTDForbidden / EntitiesForbidden or ignore it safely
    # and not return expanded file content
    locs = _extract_loc_values(malicious_xml)
    assert "/etc/passwd" not in "".join(locs)


@pytest.mark.anyio
async def test_secure_http_client_blocks_localhost_connection():
    async with SecureHttpClient() as client:
        with pytest.raises(SecurityValidationError):
            await client.fetch("http://127.0.0.1:8000/")


@pytest.mark.anyio
async def test_secure_http_client_enforces_size_limit():
    # Configure client with tiny 100-byte limit
    async with SecureHttpClient(max_html_bytes=100) as client:
        # Fetching a larger page should raise ResponseTooLargeError
        with pytest.raises(ResponseTooLargeError):
            await client.fetch("https://example.com")
