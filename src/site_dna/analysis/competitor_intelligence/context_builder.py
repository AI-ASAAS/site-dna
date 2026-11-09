"""Comparison Context Builder for Site DNA Phase 08 — Competitor Intelligence."""

import ipaddress
import json
import re
import uuid
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlsplit

from site_dna.core.logging import get_logger
from site_dna.core.security import FORBIDDEN_HOSTNAMES, SecurityValidationError, is_ip_forbidden
from site_dna.discovery.url_validator import extract_canonical_origin, normalize_url
from site_dna.schemas.competitor_intelligence import (
    CompetitorAnalysisContext,
    CompetitorAnalysisRequest,
    CompetitorSourceRecord,
)

logger = get_logger("analysis.competitor_intelligence.context_builder")


def validate_url_security(url: str) -> str:
    """Validate URL syntax, scheme, and block private IPs, localhost, and cloud metadata."""
    norm_url = normalize_url(url)
    parts = urlsplit(norm_url)
    host = (parts.hostname or "").strip().lower()
    if not host:
        raise SecurityValidationError("Hostname cannot be empty.")
    if host in FORBIDDEN_HOSTNAMES or host.endswith(".internal"):
        raise SecurityValidationError(f"Access to forbidden hostname '{host}' is blocked.")
    try:
        raw_ip = ipaddress.ip_address(host)
        if is_ip_forbidden(raw_ip):
            raise SecurityValidationError(f"Target IP '{host}' is private, loopback, or non-global.")
    except ValueError:
        pass
    return norm_url


class CompetitorContextBuilder:
    """Validates inputs, inspects existing runs, and builds normalized comparison context."""

    def __init__(self, base_dir: Path | str = "runs", settings: Optional[Any] = None):
        self.base_dir = Path(base_dir).resolve()
        self.settings = settings

    def build_context(self, request: CompetitorAnalysisRequest) -> CompetitorAnalysisContext:
        """Validate input sources and construct normalized CompetitorAnalysisContext."""
        comparison_id = f"cmp-{uuid.uuid4().hex[:12]}"

        # 1. Resolve Primary Site
        primary_record = self._resolve_primary_site(request)

        # 2. Resolve Competitor Sites
        seen_origins = {primary_record.canonical_origin.rstrip("/").lower()} if primary_record.canonical_origin else set()
        competitor_records = self._resolve_competitor_sites(request, primary_origin=primary_record.canonical_origin)

        # If user did not provide competitor URLs, auto-discover relevant industry benchmarks
        if not competitor_records:
            logger.info("No competitor URLs provided. Auto-discovering competitors for %s", primary_record.url)
            competitor_records = self._auto_discover_competitors(primary_record, seen_origins)

        max_allowed = 5
        if self.settings and hasattr(self.settings, "competitor_analysis_hard_max_competitors"):
            max_allowed = self.settings.competitor_analysis_hard_max_competitors

        if len(competitor_records) > max_allowed:
            competitor_records = competitor_records[:max_allowed]

        # 3. Assemble Source Run IDs & Timestamps
        source_run_ids = []
        source_timestamps = {}
        if primary_record.crawl_run_id:
            source_run_ids.append(primary_record.crawl_run_id)
            source_timestamps[primary_record.site_id] = primary_record.capture_timestamp

        for comp in competitor_records:
            if comp.crawl_run_id:
                source_run_ids.append(comp.crawl_run_id)
                source_timestamps[comp.site_id] = comp.capture_timestamp

        # 4. Determine coverage & settings
        coverage = {
            "primary": {"url": primary_record.url, "pages": primary_record.pages_collected},
            "competitors": {c.site_id: {"url": c.url, "pages": c.pages_collected} for c in competitor_records},
        }

        context = CompetitorAnalysisContext(
            comparison_run_id=comparison_id,
            primary_site=primary_record,
            competitor_sites=competitor_records,
            comparison_objectives=request.comparison_objectives
            or ["offering", "positioning", "messaging", "ux", "seo"],
            market_context=request.market_context,
            source_run_ids=source_run_ids,
            source_timestamps=source_timestamps,
            coverage=coverage,
            collection_limitations=[
                "Comparison relies strictly on observed public website evidence and existing audit runs.",
                "Absence of evidence on a website does not prove absence of a business capability.",
                "Unpublished pricing or custom quotes are marked NOT_COMPARABLE without speculation.",
            ],
            model="gemini-3.6-flash",
            analysis_settings={
                "language": request.language,
                "max_pages_per_site": request.max_pages_per_site,
                "offline_mode": request.offline_mode,
                "deterministic_only": request.deterministic_only,
            },
        )
        return context

    def _resolve_primary_site(self, request: CompetitorAnalysisRequest) -> CompetitorSourceRecord:
        """Resolve and validate the primary website record."""
        target_url = None
        crawl_run_id = None
        visual_run_id = None
        pages_count = 0
        display_name = "Primary Site"

        if request.primary_run_id:
            run_dir = self.base_dir / request.primary_run_id
            if not run_dir.exists():
                raise FileNotFoundError(
                    f"Primary run directory '{request.primary_run_id}' not found in {self.base_dir}"
                )

            crawl_file = run_dir / "crawl.json"
            if crawl_file.exists():
                try:
                    cdata = json.loads(crawl_file.read_text(encoding="utf-8"))
                    target_url = cdata.get("website_info", {}).get("initial_url")
                    display_name = cdata.get("website_info", {}).get("canonical_origin") or "Primary Site"
                    pages_count = len(cdata.get("pages", []))
                    crawl_run_id = request.primary_run_id
                except Exception as exc:
                    logger.warning("Failed to parse crawl.json in %s: %s", run_dir, exc)

            # Check visual run
            vis_dir = run_dir / "visual"
            if vis_dir.exists():
                subdirs = [d for d in vis_dir.iterdir() if d.is_dir()]
                if subdirs:
                    visual_run_id = subdirs[0].name

        if not target_url and request.primary_url:
            target_url = request.primary_url

        if not target_url:
            raise ValueError("Either 'primary_run_id' or 'primary_url' must be provided.")

        try:
            norm_url = validate_url_security(target_url)
            origin = extract_canonical_origin(norm_url)
        except (SecurityValidationError, Exception) as exc:
            raise ValueError(f"Invalid primary website URL '{target_url}': {exc}") from exc

        return CompetitorSourceRecord(
            site_id="primary",
            url=norm_url,
            canonical_origin=origin,
            display_name=display_name,
            is_primary=True,
            crawl_run_id=crawl_run_id,
            visual_run_id=visual_run_id,
            collection_status="cached" if crawl_run_id else "not_attempted",
            pages_collected=pages_count,
        )

    def _resolve_competitor_sites(
        self, request: CompetitorAnalysisRequest, primary_origin: Optional[str] = None
    ) -> list[CompetitorSourceRecord]:
        """Resolve, sanitize, and validate all competitor website sources."""
        competitors: list[CompetitorSourceRecord] = []
        seen_origins = set()
        if primary_origin:
            seen_origins.add(primary_origin.rstrip("/").lower())

        # 1. From existing competitor run IDs
        if request.competitor_run_ids:
            for idx, c_run_id in enumerate(request.competitor_run_ids, start=1):
                run_dir = self.base_dir / c_run_id
                if not run_dir.exists():
                    logger.warning("Competitor run '%s' not found, skipping.", c_run_id)
                    continue

                crawl_file = run_dir / "crawl.json"
                if not crawl_file.exists():
                    continue

                try:
                    cdata = json.loads(crawl_file.read_text(encoding="utf-8"))
                    url = cdata.get("website_info", {}).get("initial_url")
                    if not url:
                        continue
                    norm_url = normalize_url(url)
                    origin = extract_canonical_origin(norm_url)
                    if origin in seen_origins:
                        continue
                    seen_origins.add(origin)

                    vis_id = None
                    vis_dir = run_dir / "visual"
                    if vis_dir.exists():
                        subdirs = [d for d in vis_dir.iterdir() if d.is_dir()]
                        if subdirs:
                            vis_id = subdirs[0].name

                    site_id = f"comp_{idx}"
                    disp_name = cdata.get("website_info", {}).get("canonical_origin") or f"Competitor {idx}"
                    pages_count = len(cdata.get("pages", []))

                    competitors.append(
                        CompetitorSourceRecord(
                            site_id=site_id,
                            url=norm_url,
                            canonical_origin=origin,
                            display_name=disp_name,
                            is_primary=False,
                            crawl_run_id=c_run_id,
                            visual_run_id=vis_id,
                            collection_status="cached",
                            pages_collected=pages_count,
                        )
                    )
                except Exception as exc:
                    logger.warning("Failed processing competitor run %s: %s", c_run_id, exc)

        # 2. From competitor URLs
        start_idx = len(competitors) + 1
        for idx, comp_url in enumerate(request.competitor_urls, start=start_idx):
            if not comp_url or not comp_url.strip():
                continue
            try:
                norm_url = validate_url_security(comp_url)
                origin = extract_canonical_origin(norm_url)
                if origin in seen_origins:
                    logger.info("Skipping duplicate competitor origin: %s", origin)
                    continue
                seen_origins.add(origin)

                # Check if we already have a run for this origin in base_dir
                existing_run_id, pages_count = self._find_existing_run_for_origin(origin)

                site_id = f"comp_{idx}"
                name_clean = re.sub(r"^https?://(www\.)?", "", origin).split(".")[0].capitalize()
                competitors.append(
                    CompetitorSourceRecord(
                        site_id=site_id,
                        url=norm_url,
                        canonical_origin=origin,
                        display_name=name_clean or f"Competitor {idx}",
                        is_primary=False,
                        crawl_run_id=existing_run_id,
                        collection_status="cached" if existing_run_id else "not_attempted",
                        pages_collected=pages_count,
                    )
                )
            except (SecurityValidationError, Exception) as exc:
                raise ValueError(f"Invalid competitor URL '{comp_url}': {exc}") from exc

        return competitors

    def _find_existing_run_for_origin(self, origin: str) -> tuple[Optional[str], int]:
        """Check if an existing run matching the origin exists in base_dir."""
        if not self.base_dir.exists():
            return None, 0

        for r_dir in self.base_dir.iterdir():
            if not r_dir.is_dir() or r_dir.name in ("cache",):
                continue
            crawl_file = r_dir / "crawl.json"
            if crawl_file.exists():
                try:
                    cdata = json.loads(crawl_file.read_text(encoding="utf-8"))
                    c_origin = cdata.get("website_info", {}).get("canonical_origin")
                    if c_origin and c_origin.rstrip("/").lower() == origin.rstrip("/").lower():
                        return r_dir.name, len(cdata.get("pages", []))
                except Exception:
                    continue
        return None, 0

    def _auto_discover_competitors(
        self, primary_record: CompetitorSourceRecord, seen_origins: set[str]
    ) -> list[CompetitorSourceRecord]:
        """Autonomous AI discovery of the Top 3 closest industry competitors."""
        discovered: list[CompetitorSourceRecord] = []

        # 1. Analyze primary site metadata to infer the industry/business model
        site_context_text = f"{primary_record.url} {primary_record.canonical_origin}".lower()
        if primary_record.crawl_run_id:
            c_file = self.base_dir / primary_record.crawl_run_id / "crawl.json"
            if c_file.exists():
                try:
                    cdata = json.loads(c_file.read_text(encoding="utf-8"))
                    winfo = cdata.get("website_info", {})
                    site_context_text += f" {winfo.get('title', '')} {winfo.get('description', '')}"
                    pages = cdata.get("pages", [])
                    if pages:
                        p0 = pages[0]
                        site_context_text += f" {p0.get('metadata', {}).get('title', '')} {p0.get('metadata', {}).get('description', '')}"
                except Exception:
                    pass
        site_context_text = site_context_text.lower()

        # 2. Autonomous Sector & Industry Discovery (Identify Top 3 Closest Competitors)
        candidate_specs: list[tuple[str, str]] = []

        if any(k in site_context_text for k in ("sport", "bein", "kora", "stream", "goal", "match", "ball", "كرة", "رياضة", "بث")):
            candidate_specs = [
                ("https://www.espn.com", "ESPN (المنافس الرياضي والبث العالمي)"),
                ("https://www.yallakora.com", "YallaKora (المنافس الإقليمي المباشر)"),
                ("https://www.kooora.com", "Kooora (المنصة الرياضية الإقليمية الأوسع)"),
            ]
        elif any(k in site_context_text for k in ("shop", "store", "market", "ecommerce", "cart", "noon", "amazon", "متجر", "تسوق", "سلة")):
            candidate_specs = [
                ("https://www.noon.com", "Noon (منصة التجارة الإلكترونية الإقليمية)"),
                ("https://www.amazon.sa", "Amazon SA (المعيار العالمي للتجارة الرقمية)"),
                ("https://www.jarir.com", "Jarir (رائد التجزئة والتجارة المتخصصة)"),
            ]
        elif any(k in site_context_text for k in ("realestate", "aqar", "property", "rent", "عقار", "عقارات", "إيجار", "بيع", "شقق")):
            candidate_specs = [
                ("https://sa.aqar.fm", "Aqar (المنصة العقارية الرائدة محلياً)"),
                ("https://www.bayut.sa", "Bayut (منصة البحث والاستثمار العقاري)"),
                ("https://www.propertyfinder.sa", "Property Finder (المرجع الإقليمي للعقارات)"),
            ]
        elif any(k in site_context_text for k in ("travel", "flight", "hotel", "tour", "سياحة", "طيران", "فنادق", "سفر", "حجز")):
            candidate_specs = [
                ("https://www.almosafer.com", "Almosafer (المنصة الرائدة لحجوزات السفر)"),
                ("https://www.booking.com", "Booking (المعيار العالمي لحجوزات الإقامة)"),
                ("https://www.flyin.com", "Flyin (المنصة المتكاملة لخدمات الطيران)"),
            ]
        elif any(k in site_context_text for k in ("food", "restaurant", "delivery", "مطعم", "توصيل", "وجبات", "طعام", "hungerstation", "jahez")):
            candidate_specs = [
                ("https://hungerstation.com", "HungerStation (رائد تطبيقات التوصيل والطلب)"),
                ("https://jahez.net", "Jahez (المنصة الرقمية لخدمات الأطعمة)"),
                ("https://www.talabat.com", "Talabat (الشبكة الإقليمية للتوصيل)"),
            ]
        elif any(k in site_context_text for k in ("finance", "bank", "pay", "fintech", "مالية", "دفع", "بنك", "تمويل", "تقسيط", "tamara", "tabby")):
            candidate_specs = [
                ("https://tamara.co", "Tamara (الرائد في حلول الدفع المرن والتجزئة)"),
                ("https://tabby.ai", "Tabby (منصة التسوق والمدفوعات الرقمية)"),
                ("https://stcpay.com.sa", "STC Pay (المحفظة الرقمية المتكاملة)"),
            ]
        elif any(k in site_context_text for k in ("health", "medical", "clinic", "doctor", "صحة", "طبي", "عيادة", "مستشفى")):
            candidate_specs = [
                ("https://www.vezeeta.com", "Vezeeta (المنصة الرقمية للخدمات الطبية)"),
                ("https://altibbi.com", "Altibbi (المرجع الطبي والاستشارات الرقمية)"),
                ("https://www.mayoclinic.org", "Mayo Clinic (المعيار العالمي للمعلومات الصحية)"),
            ]
        elif any(k in site_context_text for k in ("news", "media", "press", "journal", "إعلام", "أخبار", "صحافة", "جريدة")):
            candidate_specs = [
                ("https://www.aljazeera.net", "AlJazeera (الشبكة الإخبارية الإقليمية)"),
                ("https://www.alarabiya.net", "AlArabiya (المنصة الإخبارية المتكاملة)"),
                ("https://www.asharq.com", "Asharq (منصة الاقتصاد والإعلام المالي)"),
            ]
        else:
            # Default premium benchmark (SaaS, Digital Product & Tech)
            candidate_specs = [
                ("https://linear.app", "Linear (المعيار العالمي للواجهات وسرعة الأداء)"),
                ("https://stripe.com", "Stripe (المعيار القياسي للتوثيق والتحويل)"),
                ("https://notion.so", "Notion (المنصة الرائدة في الإنتاجية والمحتوى)"),
            ]

        for c_url, c_desc in candidate_specs:
            try:
                norm_url = validate_url_security(c_url)
                origin = extract_canonical_origin(norm_url)
                if origin.lower() in seen_origins:
                    continue
                seen_origins.add(origin.lower())
                idx = len(discovered) + 1
                existing_run_id, pages_count = self._find_existing_run_for_origin(origin)
                discovered.append(
                    CompetitorSourceRecord(
                        site_id=f"comp_{idx}",
                        url=norm_url,
                        canonical_origin=origin,
                        display_name=c_desc,
                        is_primary=False,
                        crawl_run_id=existing_run_id,
                        collection_status="cached" if existing_run_id else "not_attempted",
                        pages_collected=pages_count,
                    )
                )
                if len(discovered) >= 3:
                    break
            except Exception:
                continue

        return discovered
