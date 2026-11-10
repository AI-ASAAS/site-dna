"""Shared URL normalization helpers for crawling and content extraction."""

import ipaddress
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
