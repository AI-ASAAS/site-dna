"""HTML content extractor extracting metadata, headings, text, links, buttons, images, and forms."""

import json
import re
from typing import Any, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from site_dna.core.logging import get_logger
from site_dna.discovery.url_validator import is_same_origin, normalize_url
from site_dna.schemas.page import (
    FormData,
    HeadingData,
    ImageData,
    LinkData,
    PageMetadata,
)

logger = get_logger("discovery.extractor")


class ExtractedPageContent:
    """Container holding all parsed structures from an HTML document."""

    def __init__(
        self,
        metadata: PageMetadata,
        headings: list[HeadingData],
        main_content_text: str,
        word_count: int,
        navigation_links: list[LinkData],
        all_internal_links: list[tuple[str, str]],  # (url, anchor_text)
        buttons: list[str],
        images: list[ImageData],
        forms: list[FormData],
        json_ld: list[dict[str, Any]],
    ):
        self.metadata = metadata
        self.headings = headings
        self.main_content_text = main_content_text
        self.word_count = word_count
        self.navigation_links = navigation_links
        self.all_internal_links = all_internal_links
        self.buttons = buttons
        self.images = images
        self.forms = forms
        self.json_ld = json_ld


def _clean_text(text: str) -> str:
    """Normalize internal whitespace and strip leading/trailing spaces."""
    return re.sub(r"\s+", " ", text).strip()


def extract_metadata(soup: BeautifulSoup, base_url: str) -> PageMetadata:
    """Extract document title, meta tags, and OpenGraph properties."""
    meta = PageMetadata()

    # Title
    if soup.title and soup.title.string:
        meta.title = _clean_text(soup.title.string)

    # HTML Lang
    html_tag = soup.find("html")
    if html_tag and isinstance(html_tag, Tag):
        lang = html_tag.get("lang") or html_tag.get("xml:lang")
        if isinstance(lang, str) and lang.strip():
            meta.language = lang.strip().lower()

    # Meta tags
    for tag in soup.find_all("meta"):
        if not isinstance(tag, Tag):
            continue

        name = (tag.get("name") or "").lower().strip()
        prop = (tag.get("property") or "").lower().strip()
        content = tag.get("content") or ""
        if isinstance(content, list):
            content = " ".join(content)
        content = _clean_text(content)

        if not content:
            continue

        # Standard meta
        if name == "description" and not meta.description:
            meta.description = content
        elif name == "robots" and not meta.robots_meta:
            meta.robots_meta = content
        elif name == "viewport" and not meta.viewport:
            meta.viewport = content

        # OpenGraph
        elif prop == "og:title" and not meta.og_title:
            meta.og_title = content
        elif prop == "og:description" and not meta.og_description:
            meta.og_description = content
        elif prop == "og:image" and not meta.og_image:
            meta.og_image = urljoin(base_url, content)

        # HTTP-Equiv
        equiv = (tag.get("http-equiv") or "").lower().strip()
        if equiv == "content-language" and not meta.language:
            meta.language = content.lower()
        elif "charset" in tag.attrs and not meta.charset:
            meta.charset = tag["charset"].lower()

    # Fallback description from og:description
    if not meta.description and meta.og_description:
        meta.description = meta.og_description

    # Canonical link
    canonical_tag = soup.find("link", rel=lambda r: r and "canonical" in r.lower())
    if canonical_tag and isinstance(canonical_tag, Tag) and canonical_tag.get("href"):
        href = canonical_tag["href"].strip()
        meta.canonical_url = urljoin(base_url, href)

    return meta


def extract_headings(soup: BeautifulSoup) -> list[HeadingData]:
    """Extract H1-H6 headings in document appearance order."""
    headings: list[HeadingData] = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        if not isinstance(tag, Tag):
            continue
        level = int(tag.name[1])
        text = _clean_text(tag.get_text())
        if text:
            headings.append(HeadingData(level=level, text=text))
    return headings


def extract_main_content(soup: BeautifulSoup) -> tuple[str, int]:
    """Extract clean textual content without headers, footers, scripts, or navigation boilerplate."""
    # Create clone/copy to prevent mutating original soup
    body = soup.find("body") or soup
    if not isinstance(body, Tag):
        return "", 0

    # Locate prioritized main semantic element if present
    main_el = body.find("main") or body.find("article") or body

    # Decompose non-content tags
    text_soup = BeautifulSoup(str(main_el), "lxml")
    for tag in text_soup(["script", "style", "noscript", "svg", "header", "footer", "nav", "aside", "form"]):
        tag.decompose()

    raw_text = text_soup.get_text(separator=" ")
    cleaned = _clean_text(raw_text)
    words = cleaned.split() if cleaned else []
    return cleaned, len(words)


def extract_links_and_navigation(
    soup: BeautifulSoup,
    base_url: str,
) -> tuple[list[LinkData], list[tuple[str, str]]]:
    """Extract navigation links and all discoverable internal links.

    Returns:
        (navigation_links, all_internal_links_as_url_anchor_tuples)
    """
    navigation_links: list[LinkData] = []
    all_internal_links: list[tuple[str, str]] = []
    seen_nav: set[str] = set()

    # 1. Navigation specific links
    nav_containers = soup.find_all(["nav", "header", "footer"])
    for container in nav_containers:
        for a in container.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue

            resolved = urljoin(base_url, href)
            try:
                norm = normalize_url(resolved)
            except Exception:
                continue

            anchor = _clean_text(a.get_text())
            rel = " ".join(a.get("rel", [])) if isinstance(a.get("rel"), list) else a.get("rel")
            is_internal = is_same_origin(base_url, norm)

            if norm not in seen_nav:
                seen_nav.add(norm)
                navigation_links.append(
                    LinkData(
                        url=norm,
                        text=anchor,
                        is_internal=is_internal,
                        rel=rel,
                    )
                )

    # 2. All links for crawler discovery
    seen_internal: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        resolved = urljoin(base_url, href)
        try:
            norm = normalize_url(resolved)
        except Exception:
            continue

        if is_same_origin(base_url, norm):
            if norm not in seen_internal:
                seen_internal.add(norm)
                anchor = _clean_text(a.get_text())
                all_internal_links.append((norm, anchor))

    return navigation_links, all_internal_links


def extract_buttons(soup: BeautifulSoup) -> list[str]:
    """Extract call-to-action button labels."""
    buttons: list[str] = []
    seen_btn: set[str] = set()

    for el in soup.find_all(["button", "input", "a"]):
        text = ""
        if el.name == "button":
            text = _clean_text(el.get_text())
        elif el.name == "input" and el.get("type", "").lower() in ("submit", "button"):
            text = _clean_text(el.get("value", ""))
        elif el.name == "a":
            classes = el.get("class", [])
            role = el.get("role", "")
            is_btn = role == "button" or any("btn" in c.lower() or "button" in c.lower() for c in classes)
            if is_btn:
                text = _clean_text(el.get_text())

        if text and len(text) <= 80 and text not in seen_btn:
            seen_btn.add(text)
            buttons.append(text)

    return buttons


def extract_images(soup: BeautifulSoup, base_url: str) -> list[ImageData]:
    """Extract images with src, alt, and dimension attributes."""
    images: list[ImageData] = []
    seen_src: set[str] = set()

    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if not src:
            continue

        resolved = urljoin(base_url, src.strip())
        if resolved in seen_src:
            continue
        seen_src.add(resolved)

        alt = _clean_text(img.get("alt", "")) or None

        width: Optional[int] = None
        height: Optional[int] = None
        try:
            if img.get("width") and str(img["width"]).isdigit():
                width = int(img["width"])
            if img.get("height") and str(img["height"]).isdigit():
                height = int(img["height"])
        except Exception:
            pass

        images.append(ImageData(src=resolved, alt=alt, width=width, height=height))

    return images


def extract_forms(soup: BeautifulSoup, base_url: str) -> list[FormData]:
    """Extract form structures and input names without executing submissions."""
    forms: list[FormData] = []

    for form in soup.find_all("form"):
        raw_action = form.get("action", "")
        action = urljoin(base_url, raw_action.strip()) if raw_action else base_url
        method = (form.get("method") or "GET").upper().strip()

        input_names: list[str] = []
        has_submit = False

        for inp in form.find_all(["input", "textarea", "select", "button"]):
            name = inp.get("name")
            if name and name not in input_names:
                input_names.append(name.strip())

            inp_type = (inp.get("type") or "").lower()
            if inp.name == "button" or inp_type == "submit":
                has_submit = True

        forms.append(
            FormData(
                action=action,
                method=method,
                input_names=input_names,
                has_submit_button=has_submit,
            )
        )

    return forms


def extract_json_ld(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """Parse JSON-LD structured data scripts."""
    records: list[dict[str, Any]] = []

    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue
        try:
            data = json.loads(script.string.strip())
            if isinstance(data, dict):
                records.append(data)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        records.append(item)
        except Exception:
            # Skip invalid or malformed JSON-LD gracefully
            continue

    return records


def extract_page_content(html: str, url: str) -> ExtractedPageContent:
    """Parse and extract all structured data from page HTML.

    Args:
        html: Raw HTML content string.
        url: Page URL used for resolving relative hyperlinks.

    Returns:
        ExtractedPageContent holding parsed metadata, headings, text, links, and forms.
    """
    soup = BeautifulSoup(html, "lxml")

    metadata = extract_metadata(soup, url)
    headings = extract_headings(soup)
    main_text, word_count = extract_main_content(soup)
    nav_links, internal_links = extract_links_and_navigation(soup, url)
    buttons = extract_buttons(soup)
    images = extract_images(soup, url)
    forms = extract_forms(soup, url)
    json_ld = extract_json_ld(soup)

    return ExtractedPageContent(
        metadata=metadata,
        headings=headings,
        main_content_text=main_text,
        word_count=word_count,
        navigation_links=nav_links,
        all_internal_links=internal_links,
        buttons=buttons,
        images=images,
        forms=forms,
        json_ld=json_ld,
    )
