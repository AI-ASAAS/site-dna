"""Security utilities for Site DNA: SSRF prevention, IP validation, and token authentication."""

import ipaddress
import socket

# Well-known internal hostnames and cloud metadata targets
FORBIDDEN_HOSTNAMES = frozenset(
    {
        "localhost",
        "localhost.localdomain",
        "metadata.google.internal",
        "metadata.google",
        "instance-data",
        "169.254.169.254",
    }
)

ALLOWED_SCHEMES = frozenset({"http", "https"})
ALLOWED_PORTS = frozenset({80, 443, None})


class SecurityValidationError(ValueError):
    """Raised when a URL, IP, or request fails security policies."""


def is_ip_forbidden(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Check if an IP address belongs to private, loopback, link-local, multicast, or cloud metadata.

    Handles IPv4-mapped IPv6 addresses (e.g. ::ffff:127.0.0.1) by unwrapping them.
    """
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped

    if not ip.is_global:
        return True

    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
        return True

    # Explicit check for known cloud metadata IPs
    ip_str = str(ip)
    if ip_str in {"169.254.169.254", "100.100.100.200"}:
        return True

    return False


def resolve_and_validate_host(hostname: str) -> list[str]:
    """Resolve hostname DNS and verify all returned IP addresses are publicly routable.

    Returns:
        List of verified public IP address strings.

    Raises:
        SecurityValidationError: If the host is forbidden, resolves to private/loopback/metadata IPs,
            or fails DNS resolution.
    """
    cleaned_host = hostname.strip().lower()

    if not cleaned_host:
        raise SecurityValidationError("Hostname cannot be empty.")

    if cleaned_host in FORBIDDEN_HOSTNAMES or cleaned_host.endswith(".internal"):
        raise SecurityValidationError(f"Access to forbidden hostname '{cleaned_host}' is blocked.")

    # Check if host is a raw IP literal
    try:
        raw_ip = ipaddress.ip_address(cleaned_host)
        if is_ip_forbidden(raw_ip):
            raise SecurityValidationError(f"Target IP '{cleaned_host}' is private, loopback, or non-global.")
        return [str(raw_ip)]
    except SecurityValidationError:
        raise
    except ValueError:
        # Not a raw IP literal, proceed to DNS resolution
        pass

    try:
        # Resolve all addresses (both IPv4 and IPv6)
        addr_info = socket.getaddrinfo(cleaned_host, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror as e:
        raise SecurityValidationError(f"DNS resolution failed for host '{cleaned_host}': {e}") from e

    verified_ips: list[str] = []
    seen: set[str] = set()

    for item in addr_info:
        sockaddr = item[4]
        ip_str = sockaddr[0]
        if ip_str in seen:
            continue
        seen.add(ip_str)

        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError as e:
            raise SecurityValidationError(f"Invalid resolved IP '{ip_str}' for host '{cleaned_host}': {e}") from e

        if is_ip_forbidden(ip_obj):
            raise SecurityValidationError(
                f"Host '{cleaned_host}' resolves to forbidden non-global IP '{ip_str}' (SSRF prevention)."
            )
        verified_ips.append(ip_str)

    if not verified_ips:
        raise SecurityValidationError(f"No routable IP addresses found for host '{cleaned_host}'.")

    return verified_ips
