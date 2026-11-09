"""Security & Privacy Context Builder for Site DNA Phase 09."""

import json
import re
import uuid
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlsplit

from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.core.security import SecurityValidationError
from site_dna.discovery.url_validator import extract_canonical_origin
from site_dna.schemas.security_privacy import (
    SecurityPageRecord,
    SecurityPrivacyAnalysisRequest,
    SecurityPrivacyContext,
)

logger = get_logger("analysis.security_privacy.context_builder")

SAFE_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]+$")
SENSITIVE_HEADER_KEYS = {"authorization", "proxy-authorization", "x-api-key", "cookie", "set-cookie"}


def sanitize_headers(raw_headers: dict[str, Any]) -> dict[str, str]:
    """Normalize header keys to lowercase and redact raw credentials."""
    cleaned: dict[str, str] = {}
    for k, v in raw_headers.items():
        k_lower = k.lower().strip()
        v_str = str(v).strip()
        if k_lower in SENSITIVE_HEADER_KEYS:
            if k_lower in ("cookie", "authorization", "proxy-authorization", "x-api-key"):
                cleaned[k_lower] = "[REDACTED_SECRET]"
            elif k_lower == "set-cookie":
                # For set-cookie, we preserve attribute structure without raw value
                parts = v_str.split(";")
                if parts:
                    name_eq = parts[0].split("=", 1)
                    cookie_name = name_eq[0].strip()
                    attrs = [p.strip() for p in parts[1:]]
                    cleaned[k_lower] = f"{cookie_name}=[REDACTED]; " + "; ".join(attrs)
                else:
                    cleaned[k_lower] = "[REDACTED_SECRET]"
        else:
            cleaned[k_lower] = v_str
    return cleaned


class SecurityPrivacyContextBuilder:
    """Validates inputs, inspects existing runs, and builds normalized security context."""

    def __init__(self, base_dir: Path | str = "runs", settings: Optional[Settings] = None):
        self.base_dir = Path(base_dir)
        self.settings = settings or get_settings()

    def build_context(self, request: SecurityPrivacyAnalysisRequest) -> SecurityPrivacyContext:
        """Construct normalized SecurityPrivacyContext from crawl and visual artifacts."""
        if not SAFE_ID_REGEX.match(request.crawl_run_id):
            raise SecurityValidationError(f"Invalid crawl_run_id format: '{request.crawl_run_id}'")

        if request.visual_run_id and not SAFE_ID_REGEX.match(request.visual_run_id):
            raise SecurityValidationError(f"Invalid visual_run_id format: '{request.visual_run_id}'")

        # Resolve runs directory safely
        runs_dir = self.base_dir
        crawl_dir = (runs_dir / request.crawl_run_id).resolve()

        if not str(crawl_dir).startswith(str(runs_dir.resolve())):
            raise SecurityValidationError("Path traversal detected in crawl_run_id.")

        if not crawl_dir.exists():
            raise FileNotFoundError(f"Crawl run directory not found: {crawl_dir}")

        crawl_file = crawl_dir / "crawl.json"
        if not crawl_file.exists():
            raise FileNotFoundError(f"Crawl data file missing: {crawl_file}")

        try:
            crawl_data = json.loads(crawl_file.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ValueError(f"Corrupt or unreadable crawl.json: {exc}") from exc

        primary_url = crawl_data.get("target_url") or crawl_data.get("url") or ""
        if not primary_url:
            pages = crawl_data.get("pages", [])
            if pages:
                primary_url = pages[0].get("url", "")

        site_origin = extract_canonical_origin(primary_url) if primary_url else "unknown_origin"
        security_run_id = f"sec-{uuid.uuid4().hex[:12]}"

        # Load optional visual evidence
        if request.visual_run_id:
            visual_dir = (runs_dir / request.visual_run_id).resolve()
            if visual_dir.exists() and str(visual_dir).startswith(str(runs_dir.resolve())):
                manifest_file = visual_dir / "manifest.json"
                if manifest_file.exists():
                    try:
                        json.loads(manifest_file.read_text(encoding="utf-8"))
                    except Exception as e:
                        logger.warning("Could not read visual manifest: %s", e)

        raw_pages = crawl_data.get("pages", [])
        page_records: list[SecurityPageRecord] = []

        for p in raw_pages[: request.max_pages]:
            p_url = p.get("url", "")
            if not p_url:
                continue

            parts = urlsplit(p_url)
            scheme = parts.scheme.lower() or "https"
            status_code = p.get("status_code", 200)

            # Headers
            raw_headers = p.get("headers", {}) or {}
            headers = sanitize_headers(raw_headers)

            # Raw cookies
            raw_cookies = p.get("cookies", []) or []
            safe_cookies: list[dict[str, Any]] = []
            for c in raw_cookies:
                if isinstance(c, dict):
                    c_clean = dict(c)
                    c_clean["value"] = "[REDACTED]"
                    safe_cookies.append(c_clean)

            # Mixed content & third parties
            html = p.get("raw_html", "") or p.get("html", "") or ""
            mixed_content = self._extract_mixed_content_candidates(html, scheme)
            third_parties = self._extract_third_party_origins(html, site_origin)

            # Privacy & cookie banner signals in text or DOM
            text_lower = (p.get("text", "") or "").lower()
            html_lower = html.lower()
            has_privacy = bool(
                "privacy" in text_lower
                or "privacy-policy" in html_lower
                or "سياسة الخصوصية" in text_lower
                or "/privacy" in html_lower
            )
            has_banner = bool(
                "cookie" in html_lower
                and ("banner" in html_lower or "consent" in html_lower or "إشعار ملفات تعريف الارتباط" in text_lower)
            )

            record = SecurityPageRecord(
                page_url=p_url,
                canonical_url=p.get("canonical_url"),
                scheme=scheme,
                status_code=status_code,
                headers=headers,
                cookies=safe_cookies,
                mixed_content_resources=mixed_content,
                third_party_origins=third_parties,
                has_privacy_link=has_privacy,
                has_cookie_banner=has_banner,
            )
            page_records.append(record)

        logger.info(
            "Constructed SecurityPrivacyContext for %s with %d pages",
            site_origin,
            len(page_records),
        )

        return SecurityPrivacyContext(
            security_run_id=security_run_id,
            source_crawl_run_id=request.crawl_run_id,
            source_visual_run_id=request.visual_run_id,
            site_origin=site_origin,
            target_url=primary_url,
            page_records=page_records,
            raw_evidence_count=len(page_records),
        )

    def _extract_mixed_content_candidates(self, html: str, page_scheme: str) -> list[str]:
        """Detect HTTP resource URLs inside an HTTPS page."""
        if page_scheme != "https":
            return []
        matches = re.findall(r"""(?:src|href)=['"](http://[^'"\s>]+)['"]""", html, re.IGNORECASE)
        # Strip query strings from candidate URLs to prevent secret leakage
        sanitized: list[str] = []
        for m in matches:
            clean_m = m.split("?")[0].split("#")[0]
            if clean_m not in sanitized:
                sanitized.append(clean_m)
        return sanitized[:20]

    def _extract_third_party_origins(self, html: str, site_origin: str) -> list[str]:
        """Extract external origins from script, link, and img tags."""
        matches = re.findall(r"""(?:src|href)=['"]((?:https?:)?//[^/'"\s>]+)""", html, re.IGNORECASE)
        origins: list[str] = []
        site_host = urlsplit(site_origin).hostname or site_origin
        for m in matches:
            if m.startswith("//"):
                m = "https:" + m
            parts = urlsplit(m)
            host = parts.hostname or ""
            if host and host.lower() != site_host.lower() and not host.endswith("." + site_host.lower()):
                origin = f"{parts.scheme or 'https'}://{host}"
                if origin not in origins:
                    origins.append(origin)
        return origins[:30]
