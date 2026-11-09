"""Accessibility Context Builder for Site DNA Phase 10."""

import json
import re
import uuid
from pathlib import Path
from typing import Any, Optional

from bs4 import BeautifulSoup

from site_dna.analysis.accessibility.sampling import RepresentativeSampler
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.core.security import SecurityValidationError
from site_dna.discovery.url_validator import extract_canonical_origin
from site_dna.schemas.accessibility import (
    AccessibilityAnalysisRequest,
    AccessibilityContext,
    AccessibilityPageRecord,
)

logger = get_logger("analysis.accessibility.context_builder")


def validate_crawl_run_id(crawl_run_id: str) -> str:
    """Validate crawl run identifier to prevent path traversal and injection."""
    if not crawl_run_id or not isinstance(crawl_run_id, str):
        raise ValueError("crawl_run_id must be a non-empty string")
    safe_pattern = re.compile(r"^[a-zA-Z0-9_\-]+$")
    if not safe_pattern.match(crawl_run_id):
        raise ValueError(f"Invalid characters in crawl_run_id: '{crawl_run_id}'")
    return crawl_run_id


class AccessibilityContextBuilder:
    """Constructs normalized runtime context for accessibility & WCAG evaluation."""

    def __init__(self, base_dir: Path | str = "runs", settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.base_dir = Path(base_dir)
        self.sampler = RepresentativeSampler()

    def build_context(self, request: AccessibilityAnalysisRequest) -> AccessibilityContext:
        """Load, validate, and structure crawl and browser data into an AccessibilityContext."""
        # Validate ID formats against path traversal attacks
        safe_id_pattern = re.compile(r"^[a-zA-Z0-9_\-]+$")
        if not safe_id_pattern.match(request.crawl_run_id):
            raise SecurityValidationError(f"Invalid crawl_run_id format: '{request.crawl_run_id}'")

        if request.visual_run_id and not safe_id_pattern.match(request.visual_run_id):
            raise SecurityValidationError(f"Invalid visual_run_id format: '{request.visual_run_id}'")

        if request.ux_run_id and not safe_id_pattern.match(request.ux_run_id):
            raise SecurityValidationError(f"Invalid ux_run_id format: '{request.ux_run_id}'")

        runs_dir = self.base_dir
        crawl_dir = (runs_dir / request.crawl_run_id).resolve()
        if not crawl_dir.exists() or not str(crawl_dir).startswith(str(runs_dir.resolve())):
            raise FileNotFoundError(f"Crawl run directory not found or unauthorized: '{request.crawl_run_id}'")

        crawl_file = crawl_dir / "crawl.json"
        if not crawl_file.exists():
            raise FileNotFoundError(f"Crawl dataset 'crawl.json' missing in: '{request.crawl_run_id}'")

        try:
            crawl_data: dict[str, Any] = json.loads(crawl_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error("Failed to parse crawl.json: %s", e)
            raise ValueError(f"Corrupt crawl.json in {request.crawl_run_id}") from e

        # Extract origin and primary metadata
        primary_url = crawl_data.get("website_info", {}).get("initial_url", "")
        if not primary_url and crawl_data.get("pages"):
            primary_url = crawl_data["pages"][0].get("url", "")

        site_origin = extract_canonical_origin(primary_url) if primary_url else "unknown_origin"
        accessibility_run_id = f"a11y-{uuid.uuid4().hex[:12]}"

        # Parse raw pages into AccessibilityPageRecord
        raw_pages = crawl_data.get("pages", [])
        page_records: list[AccessibilityPageRecord] = []

        for p in raw_pages:
            p_url = p.get("url", "")
            if not p_url:
                continue

            raw_html = p.get("raw_html") or p.get("html") or ""
            soup = BeautifulSoup(raw_html, "html.parser") if raw_html else None

            doc_lang = None
            doc_dir = None
            headings_count = 0
            landmarks_count = 0
            links_count = len(p.get("links", []))
            images_count = 0
            form_controls_count = 0
            interactive_count = 0

            if soup:
                html_tag = soup.find("html")
                if html_tag:
                    doc_lang = html_tag.get("lang")
                    doc_dir_val = (html_tag.get("dir") or "").lower()
                    if doc_dir_val in ("rtl", "ltr", "auto"):
                        doc_dir = doc_dir_val  # type: ignore

                headings_count = len(soup.find_all(re.compile(r"^h[1-6]$")))
                landmarks_count = len(soup.find_all(["main", "nav", "header", "footer", "aside", "form", "section"]))
                images_count = len(soup.find_all("img")) + len(soup.find_all("svg"))
                form_controls_count = len(soup.find_all(["input", "select", "textarea", "button"]))
                interactive_count = (
                    len(soup.find_all(["a", "button", "input", "select", "textarea"]))
                    + len(soup.find_all(attrs={"tabindex": True}))
                    + len(soup.find_all(attrs={"role": "button"}))
                )

            page_title = p.get("title")
            if not page_title and soup and soup.title:
                page_title = soup.title.string

            rec = AccessibilityPageRecord(
                page_url=p_url,
                page_title=page_title,
                status_code=p.get("status_code", 200),
                document_language=doc_lang,
                document_direction=doc_dir,
                viewport={"width": 1280, "height": 800},
                screenshot_path=p.get("screenshot_path"),
                dom_snapshot_ref=p.get("dom_snapshot_ref"),
                accessibility_tree_ref=p.get("accessibility_tree_ref"),
                interactive_elements_count=interactive_count,
                form_controls_count=form_controls_count,
                images_count=images_count,
                links_count=links_count,
                headings_count=headings_count,
                landmarks_count=landmarks_count,
            )
            page_records.append(rec)

        # 3. Apply representative sampling (Step 02)
        sampling_plan = self.sampler.select_sample(page_records, max_pages=request.max_pages)

        return AccessibilityContext(
            accessibility_run_id=accessibility_run_id,
            crawl_run_id=request.crawl_run_id,
            visual_run_id=request.visual_run_id,
            ux_run_id=request.ux_run_id,
            target_url=primary_url,
            site_origin=site_origin,
            page_records=sampling_plan.sampled_pages,
            sampling_record=sampling_plan,
        )
