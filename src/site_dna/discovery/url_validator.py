"""URL validation, normalization, and origin matching for Site DNA crawler."""

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from site_dna.core.security import (
    ALLOWED_PORTS,
    ALLOWED_SCHEMES,
    SecurityValidationError,
    resolve_and_validate_host,
)

TRACKING_QUERY_PARAMS = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "gclid",
        "fbclid",
        "msclkid",
        "mc_cid",
        "mc_eid",
        "_ga",
        "_gl",
        "trk",
        "ref",
        "source",
    }
)


def normalize_url(url: str) -> str:
    """Normalize and validate a URL against SSRF and syntax rules.

    Rules:
        - Defaults to https:// if no scheme is specified.
        - Schemes restricted to http and https.
        - Reject embedded credentials (user:pass@host).
        - Restrict ports to standard 80 and 443.
        - Strips fragments (#...).
        - Ensures root path '/' if path is empty.
        - Lowercases scheme and hostname.

    Raises:
        SecurityValidationError: If the URL fails security constraints.
    """
    cleaned = url.strip()
    if not cleaned:
        raise SecurityValidationError("Target URL cannot be empty.")

    # Check for scheme presence
    if "://" in cleaned:
        raw_scheme = cleaned.split("://", 1)[0].lower()
        if raw_scheme not in ALLOWED_SCHEMES:
            raise SecurityValidationError(f"Disallowed scheme '{raw_scheme}'. Only http and https are allowed.")
    elif cleaned.startswith("//"):
        cleaned = "https:" + cleaned
    elif ":" in cleaned.split("/", 1)[0]:
        raw_scheme = cleaned.split(":", 1)[0].lower()
        if raw_scheme not in ALLOWED_SCHEMES:
            raise SecurityValidationError(f"Disallowed scheme '{raw_scheme}'. Only http and https are allowed.")
    else:
        cleaned = "https://" + cleaned

    try:
        parts = urlsplit(cleaned)
    except Exception as e:
        raise SecurityValidationError(f"Invalid URL structure: {e}") from e

    scheme = parts.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise SecurityValidationError(f"Disallowed scheme '{parts.scheme}'. Only http and https are allowed.")

    netloc = parts.netloc.strip()
    if not netloc:
        raise SecurityValidationError("URL must include a valid hostname/domain.")

    # Reject embedded user info / credentials
    if "@" in netloc or parts.username or parts.password:
        raise SecurityValidationError("URLs with embedded user credentials (user:pass@) are prohibited.")

    # Validate port
    port = parts.port
    if port is not None and port not in ALLOWED_PORTS:
        raise SecurityValidationError(f"Port {port} is not permitted. Only ports 80 and 443 are allowed.")

    hostname = parts.hostname
    if not hostname:
        raise SecurityValidationError("URL has no resolvable hostname.")

    hostname = hostname.lower()

    # Reconstruct normalized netloc
    if port and port not in (80 if scheme == "http" else 443, None):
        normalized_netloc = f"{hostname}:{port}"
    else:
        normalized_netloc = hostname

    # Normalize path
    path = parts.path or "/"

    # Normalize query: strip tracking parameters, sort parameters
    query_params = parse_qsl(parts.query, keep_blank_values=True)
    filtered_params = [(k, v) for k, v in query_params if k.lower() not in TRACKING_QUERY_PARAMS]
    filtered_query = urlencode(filtered_params)

    # Rebuild URL with fragment omitted
    normalized = urlunsplit((scheme, normalized_netloc, path, filtered_query, ""))
    return normalized


def extract_canonical_origin(url: str) -> str:
    """Extract the canonical origin (scheme + netloc without default port) from a URL."""
    norm = normalize_url(url)
    parts = urlsplit(norm)
    return f"{parts.scheme}://{parts.netloc}"


def is_same_origin(source_url: str, target_url: str) -> bool:
    """Check if target_url belongs to the same origin (scheme, host, port) as source_url."""
    try:
        source_origin = extract_canonical_origin(source_url)
        target_origin = extract_canonical_origin(target_url)
        return source_origin.lower() == target_origin.lower()
    except SecurityValidationError:
        return False


def validate_url_and_resolve(url: str) -> tuple[str, list[str]]:
    """Validate URL syntax and resolve DNS, verifying all resolved IPs are public.

    Returns:
        Tuple of (normalized_url, list_of_verified_ips).

    Raises:
        SecurityValidationError: If validation or DNS checks fail.
    """
    normalized = normalize_url(url)
    parts = urlsplit(normalized)
    assert parts.hostname is not None
    verified_ips = resolve_and_validate_host(parts.hostname)
    return normalized, verified_ips
