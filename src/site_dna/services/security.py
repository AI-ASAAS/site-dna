"""URL validation and SSRF-safe IP policy for the Website Intelligence MVP (Phase 2)."""

import asyncio
import ipaddress
import socket
from dataclasses import dataclass
from typing import Awaitable, Callable, Iterable, Optional
from urllib.parse import urlsplit, urlunsplit

from site_dna.core.security import SecurityValidationError, is_ip_forbidden, resolve_and_validate_host

DEFAULT_ALLOWED_PORTS = frozenset({80, 443})
ALLOWED_SCHEMES = frozenset({"http", "https"})
FORBIDDEN_HOSTNAMES = frozenset(
    {
        "localhost",
        "localhost.localdomain",
        "metadata.google.internal",
        "metadata.google",
        "instance-data",
    }
)
FORBIDDEN_HOST_SUFFIXES = (".local", ".internal", ".localdomain")

IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address
AsyncResolver = Callable[[str], Awaitable[list[str]]]


@dataclass(frozen=True)
class ValidatedUrl:
    """A URL that passed syntax, SSRF, and DNS validation."""

    url: str
    scheme: str
    host: str
    port: int
    ips: list[str]


class UrlRejected(Exception):
    """Raised when a URL fails validation. `code` is a stable machine-readable reason."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def is_ip_allowed(ip: str | IPAddress) -> bool:
    """Pure predicate: return True only for globally routable IP addresses."""
    try:
        parsed = ipaddress.ip_address(ip.strip()) if isinstance(ip, str) else ip
    except ValueError:
        return False
    return not is_ip_forbidden(parsed)


def _default_port(scheme: str) -> int:
    return 80 if scheme == "http" else 443


def _ensure_scheme(raw: str) -> str:
    cleaned = raw.strip()
    if not cleaned:
        raise UrlRejected("empty_url", "Target URL cannot be empty.")

    if "://" in cleaned:
        scheme = cleaned.split("://", 1)[0].lower()
    elif cleaned.startswith("//"):
        cleaned = "https:" + cleaned
        scheme = "https"
    elif ":" in cleaned.split("/", 1)[0]:
        scheme = cleaned.split(":", 1)[0].lower()
    else:
        cleaned = "https://" + cleaned
        scheme = "https"

    if scheme not in ALLOWED_SCHEMES:
        raise UrlRejected(
            "invalid_scheme",
            f"Disallowed scheme '{scheme}'. Only http and https are allowed.",
        )
    return cleaned


def _normalize_host(raw_host: str) -> str:
    host = raw_host.strip().lower()
    if not host:
        raise UrlRejected("invalid_url", "URL has no hostname.")

    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        pass

    try:
        return host.encode("idna").decode("ascii").lower()
    except UnicodeError as e:
        raise UrlRejected("invalid_url", f"Hostname '{host}' cannot be IDNA-encoded: {e}") from e


def _check_hostname(host: str) -> None:
    if host in FORBIDDEN_HOSTNAMES or any(host.endswith(suffix) for suffix in FORBIDDEN_HOST_SUFFIXES):
        raise UrlRejected("forbidden_hostname", f"Access to forbidden hostname '{host}' is blocked.")


def _resolve_all(host: str) -> list[str]:
    """Resolve all A/AAAA records without rejecting private addresses."""
    try:
        ipaddress.ip_address(host)
        return [host]
    except ValueError:
        pass

    try:
        addr_info = socket.getaddrinfo(host, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror as e:
        raise UrlRejected("dns_error", f"DNS resolution failed for host '{host}': {e}") from e

    ips: list[str] = []
    for item in addr_info:
        ip = str(item[4][0])
        if ip not in ips:
            ips.append(ip)
    if not ips:
        raise UrlRejected("dns_error", f"No addresses found for host '{host}'.")
    return ips


def _private_hosts_enabled(explicit: Optional[bool]) -> bool:
    if explicit is not None:
        return explicit
    from site_dna.core.config import get_settings

    return get_settings().private_hosts_allowed()


def _netloc_for(host: str, port: int, scheme: str) -> str:
    try:
        is_ipv6 = isinstance(ipaddress.ip_address(host), ipaddress.IPv6Address)
    except ValueError:
        is_ipv6 = False

    rendered_host = f"[{host}]" if is_ipv6 else host
    if port != _default_port(scheme):
        return f"{rendered_host}:{port}"
    return rendered_host


async def _resolve(
    host: str,
    resolver: Optional[AsyncResolver],
    allow_private: bool,
) -> list[str]:
    if resolver is not None:
        try:
            return await resolver(host)
        except UrlRejected:
            raise
        except SecurityValidationError as e:
            raise UrlRejected("forbidden_ip", str(e)) from e
        except Exception as e:
            raise UrlRejected("dns_error", f"DNS resolution failed for host '{host}': {e}") from e

    try:
        if allow_private:
            return await asyncio.to_thread(_resolve_all, host)
        return await asyncio.to_thread(resolve_and_validate_host, host)
    except UrlRejected:
        raise
    except SecurityValidationError as e:
        raise UrlRejected("forbidden_ip", str(e)) from e


async def validate_url(
    raw: str,
    *,
    allow_private_hosts: Optional[bool] = None,
    allowed_ports: Optional[Iterable[int]] = None,
    resolver: Optional[AsyncResolver] = None,
) -> ValidatedUrl:
    """Validate a URL for safe outbound fetching.

    Enforces scheme, credential, port, hostname, and DNS/IP rules. Every resolved
    address must be publicly routable unless private hosts are explicitly enabled
    (only honored when APP_ENV=test via settings).

    Raises:
        UrlRejected: with a stable `code` describing the failure.
    """
    cleaned = _ensure_scheme(raw)

    try:
        parts = urlsplit(cleaned)
    except ValueError as e:
        raise UrlRejected("invalid_url", f"Invalid URL structure: {e}") from e

    scheme = parts.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise UrlRejected("invalid_scheme", f"Disallowed scheme '{scheme}'.")

    if "@" in parts.netloc or parts.username or parts.password:
        raise UrlRejected("credentials_not_allowed", "URLs with embedded credentials are prohibited.")

    if not parts.hostname:
        raise UrlRejected("invalid_url", "URL has no hostname.")

    host = _normalize_host(parts.hostname)
    _check_hostname(host)

    try:
        raw_port = parts.port
    except ValueError as e:
        raise UrlRejected("port_not_allowed", f"Invalid port in URL: {e}") from e

    port = raw_port if raw_port is not None else _default_port(scheme)
    permitted_ports = set(allowed_ports) if allowed_ports is not None else set(DEFAULT_ALLOWED_PORTS)
    if port not in permitted_ports:
        raise UrlRejected(
            "port_not_allowed",
            f"Port {port} is not permitted. Allowed ports: {sorted(permitted_ports)}.",
        )

    allow_private = _private_hosts_enabled(allow_private_hosts)
    ips = await _resolve(host, resolver, allow_private)

    if not allow_private:
        for ip in ips:
            if not is_ip_allowed(ip):
                raise UrlRejected(
                    "forbidden_ip",
                    f"Host '{host}' resolves to forbidden non-public IP '{ip}'.",
                )

    normalized = urlunsplit(
        (
            scheme,
            _netloc_for(host, port, scheme),
            parts.path or "/",
            parts.query,
            "",
        )
    )
    return ValidatedUrl(url=normalized, scheme=scheme, host=host, port=port, ips=ips)
