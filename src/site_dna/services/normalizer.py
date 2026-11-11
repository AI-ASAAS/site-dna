"""Shared URL normalization helpers for crawling and content extraction."""

import ipaddress
import math
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import tldextract

TRACKING_QUERY_PARAMS = frozenset(
    {
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

NON_HTML_EXTENSIONS = frozenset(
    {
        ".pdf",
        ".zip",
        ".rar",
        ".gz",
        ".tar",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".webp",
        ".ico",
        ".mp4",
        ".mp3",
        ".avi",
        ".mov",
        ".wav",
        ".css",
        ".js",
        ".json",
        ".xml",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
    }
)

_extractor = tldextract.TLDExtract(suffix_list_urls=())


def registrable_domain(host: str) -> str:
    """Return the registrable domain for a host, falling back to the host itself."""
    extracted = _extractor(host.lower())
    if extracted.domain and extracted.suffix:
        return f"{extracted.domain}.{extracted.suffix}".lower()
    return host.lower()


def is_non_html_url(url: str) -> bool:
    """Return True when the URL path ends with a known non-HTML extension."""
    path = urlsplit(url).path.lower()
    return any(path.endswith(extension) for extension in NON_HTML_EXTENSIONS)


def strip_fragment(url: str) -> str:
    """Remove the fragment component from a URL."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))


def canonicalize_url(url: str) -> str:
    """Canonicalize a URL for deduplication.

    Drops fragments, removes tracking parameters, sorts query parameters, removes
    default ports, and normalizes trailing slashes (except for the root path).
    """
    parts = urlsplit(url)
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    port = parts.port
    default_port = 80 if scheme == "http" else 443

    try:
        is_ipv6 = isinstance(ipaddress.ip_address(host), ipaddress.IPv6Address)
    except ValueError:
        is_ipv6 = False
    rendered_host = f"[{host}]" if is_ipv6 else host
    netloc = rendered_host if port in (None, default_port) else f"{rendered_host}:{port}"

    path = parts.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/") or "/"

    filtered = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in TRACKING_QUERY_PARAMS
    ]
    query = urlencode(sorted(filtered))

    return urlunsplit((scheme, netloc, path, query, ""))


def normalize_url(url: str | None) -> str | None:
    """Return a trimmed, canonical absolute URL, or ``None`` for missing input."""
    if url is None:
        return None
    value = url.strip()
    if not value:
        return None
    parts = urlsplit(value)
    if not parts.scheme or not parts.netloc:
        return value
    return canonicalize_url(value)


def normalize_text(value: str | None) -> str | None:
    """Collapse whitespace and return ``None`` for empty text."""
    if value is None:
        return None
    normalized = " ".join(value.split())
    return normalized or None


def normalize_number(value: object) -> int | float | None:
    """Return a finite number, accepting numeric strings; booleans are ignored."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = value
    elif isinstance(value, str):
        try:
            number = float(value.strip())
        except ValueError:
            return None
    else:
        return None
    if not math.isfinite(number):
        return None
    return int(number) if isinstance(number, float) and number.is_integer() else number


def normalize_list(values: object) -> list:
    """Return a deduplicated list copy, dropping ``None`` entries and preserving order."""
    if values is None:
        return []
    raw = list(values) if isinstance(values, (list, tuple, set)) else [values]
    result: list = []
    seen: set[str] = set()
    for value in raw:
        if value is None:
            continue
        key = repr(value)
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def sort_colors_by_weight(colors: object) -> list:
    """Sort color records by descending weight, keeping unweighted entries last."""
    records = normalize_list(colors)
    return sorted(records, key=lambda color: -(normalize_number(getattr(color, "weight", None)) or 0))


def normalize_issue(
    rule_id: str,
    *,
    url: str | None = None,
    message: str | None = None,
    confidence: str | None = None,
) -> dict:
    """Normalize an actionable issue to the report's flat issue shape."""
    return {
        "id": rule_id,
        "url": normalize_url(url),
        "message": normalize_text(message),
        "confidence": confidence,
    }
