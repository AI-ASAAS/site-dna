"""Heuristic noise removal rules shared by local parsing and Crawl4AI."""

EXCLUDED_TAGS = (
    "script",
    "style",
    "noscript",
    "nav",
    "footer",
    "aside",
    "form",
    "svg",
    "iframe",
    "template",
)

EXCLUDED_SELECTORS = (
    "[role='navigation']",
    "[role='banner']",
    "[role='contentinfo']",
    ".cookie-banner",
    ".cookie-consent",
    ".newsletter",
    ".advertisement",
    ".ad",
)

EXCLUDED_SELECTOR = ", ".join(EXCLUDED_SELECTORS)
