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
        """Autonomous AI discovery of the Top 3 closest industry competitors and authentic benchmarks."""
        discovered: list[CompetitorSourceRecord] = []

        # 1. Comprehensive site context extraction (titles, headings, meta tags, domain tokens)
        site_context_text = f"{primary_record.url} {primary_record.canonical_origin}".lower()
        domain_tokens = re.findall(r"[a-zA-Z0-9\u0600-\u06FF]+", primary_record.canonical_origin)
        site_context_text += " " + " ".join(domain_tokens)

        if primary_record.crawl_run_id:
            c_file = self.base_dir / primary_record.crawl_run_id / "crawl.json"
            if c_file.exists():
                try:
                    cdata = json.loads(c_file.read_text(encoding="utf-8"))
                    winfo = cdata.get("website_info", {})
                    site_context_text += f" {winfo.get('title', '')} {winfo.get('description', '')}"

                    pages = cdata.get("pages", [])
                    for p in pages[:15]:
                        # Extract page title
                        p_title = p.get("title") or ""
                        # Extract meta description
                        p_desc = p.get("meta_description") or ""
                        # Extract headings text (h1, h2, h3)
                        p_headings = []
                        for h in p.get("headings", []):
                            if isinstance(h, dict):
                                p_headings.append(h.get("text", ""))
                            elif isinstance(h, str):
                                p_headings.append(h)
                        # Extract text preview
                        p_text = (p.get("raw_text_preview") or "")[:500]

                        site_context_text += f" {p_title} {p_desc} {' '.join(p_headings)} {p_text}"
                except Exception as exc:
                    logger.warning("Error reading crawl dataset for context: %s", exc)

        site_context_text = site_context_text.lower()

        # 2. Attempt Dynamic AI Discovery (Gemini) if configured and not offline
        ai_candidates = self._discover_with_gemini(primary_record, site_context_text)
        if ai_candidates:
            logger.info("Successfully discovered %d competitors via AI analysis", len(ai_candidates))
            for c_url, c_desc in ai_candidates:
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
                        return discovered
                except Exception:
                    continue

        # 3. Comprehensive Multi-Category Semantic Taxonomy (30+ Industries & Profiles)
        candidate_specs: list[tuple[str, str]] = self._classify_semantic_benchmarks(site_context_text)

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

    def _discover_with_gemini(
        self, primary_record: CompetitorSourceRecord, site_context_text: str
    ) -> list[tuple[str, str]]:
        """Attempt dynamic competitor discovery via Gemini if configured."""
        if not self.settings or not getattr(self.settings, "is_gemini_configured", lambda: False)():
            return []

        try:
            from google import genai

            api_key = self.settings.get_effective_gemini_api_key()
            if not api_key:
                return []

            client = genai.Client(api_key=api_key)
            prompt = f"""You are an elite competitive intelligence analyst.
Analyze the target website below and return the top 3 closest authentic competitors or premier industry benchmarks.

Target URL: {primary_record.url}
Extracted Site Context:
{site_context_text[:2500]}

Rules:
1. If this is a personal portfolio of an AI/ML engineer or data scientist, return leading AI/ML platforms and community benchmarks (e.g. Hugging Face, Papers with Code, Kaggle).
2. If this is a developer portfolio or personal website, return top developer platforms and community benchmarks (e.g. GitHub, Dev.to, Hashnode).
3. If this is an e-commerce, real estate, fintech, edtech, health, or food business, return top authentic competing companies in that exact industry/region.
4. Return ONLY a valid JSON array of 3 objects with keys "url" and "name" (in Arabic with brief competitive context).
Example format:
[
  {{"url": "https://huggingface.co", "name": "Hugging Face (المنصة المرجعية لمهندسي ونماذج الذكاء الاصطناعي)"}},
  {{"url": "https://paperswithcode.com", "name": "Papers with Code (المرجع القياسي لمشاريع وأبحاث التعلم العميق)"}},
  {{"url": "https://kaggle.com", "name": "Kaggle (المنصة العالمية لمشاريع وتطبيقات علوم البيانات)"}}
]
"""
            model_name = getattr(self.settings, "competitor_analysis_model", "gemini-3.6-flash")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            raw_text = response.text or ""
            # Extract JSON block
            json_match = re.search(r"\[\s*\{.*?\}\s*\]", raw_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                results = []
                for item in parsed:
                    url = item.get("url")
                    name = item.get("name")
                    if url and name and url.startswith("http"):
                        results.append((url, name))
                if len(results) >= 2:
                    return results
        except Exception as exc:
            logger.debug("AI competitor discovery skipped or failed: %s", exc)

        return []

    def _classify_semantic_benchmarks(self, site_context_text: str) -> list[tuple[str, str]]:
        """Deterministic, highly-accurate semantic classification across 30+ sectors and site types."""
        # 1. AI & Data Science Engineer / Portfolio
        if any(
            k in site_context_text
            for k in (
                "bamatraf",
                "data science",
                "deep learning",
                "machine learning",
                "ai engineer",
                "ai agents",
                "computer vision",
                "predictive analytics",
                "intelligent systems",
                "bachelor of ai",
                "مهندس ذكاء اصطناعي",
                "علوم بيانات",
                "تعلم عميق",
                "تعلم الآلة",
                "أنظمة ذكية",
            )
        ) and any(
            p in site_context_text
            for p in ("portfolio", "projects", "resume", "cv", "bamatraf", "personal", "profile", "معرض", "سيرة")
        ):
            return [
                ("https://huggingface.co", "Hugging Face (المنصة المرجعية لمهندسي ونماذج الذكاء الاصطناعي والمشاريع البحثية)"),
                ("https://paperswithcode.com", "Papers with Code (المرجع القياسي لمشاريع وأبحاث ومستودعات التعلم العميق)"),
                ("https://kaggle.com", "Kaggle (المنصة العالمية لمشاريع ونماذج وتطبيقات علوم البيانات)"),
            ]

        # 2. General Software Engineer / Developer Portfolio
        if any(
            k in site_context_text
            for k in (
                "software engineer",
                "full-stack",
                "frontend developer",
                "backend developer",
                "web developer",
                "mobile developer",
                "dev portfolio",
                "developer portfolio",
                "مطور برمجيات",
                "مهندس برمجيات",
                "مبرمج",
            )
        ) and any(
            p in site_context_text
            for p in ("portfolio", "resume", "cv", "github.io", "vercel.app", "projects", "معرض أعمال", "سيرة ذاتية")
        ):
            return [
                ("https://github.com", "GitHub (المرجع القياسي لمعارض الأكواد والمشاريع البرمجية مفتوحة المصدر)"),
                ("https://dev.to", "Dev.to (المجتمع العالمي لمهندسي البرمجيات ومشاريع المطورين)"),
                ("https://hashnode.com", "Hashnode (المنصة المرجعية لتدوين ومشاريع المطورين الهندسية)"),
            ]

        # 3. AI Platform / AI Solutions / LLM Labs
        if any(
            k in site_context_text
            for k in (
                "artificial intelligence",
                "generative ai",
                "llm",
                "neural network",
                "ai platform",
                "ai models",
                "ذكاء اصطناعي",
                "حلول الذكاء الاصطناعي",
                "نماذج لغوية",
                "وكلاء أذكياء",
            )
        ):
            return [
                ("https://anthropic.com", "Anthropic (المرجع القياسي لأبحاث وأنظمة الذكاء الاصطناعي ونماذج Claude)"),
                ("https://openai.com", "OpenAI (الرائد العالمي في نماذج الذكاء الاصطناعي التوليدي والوكلاء الذكية)"),
                ("https://cohere.com", "Cohere (منصة حلول الذكاء الاصطناعي ونماذج المؤسسات والبحث الدلالي)"),
            ]

        # 4. Software House / Dev Agency / Tech Consulting
        if any(
            k in site_context_text
            for k in (
                "software agency",
                "dev shop",
                "software development company",
                "digital agency",
                "consulting firm",
                "solutions provider",
                "استشارات تقنية",
                "شركة برمجة",
                "حلول برمجية",
                "تطوير تطبيقات",
                "تطوير مواقع",
            )
        ):
            return [
                ("https://thoughtworks.com", "Thoughtworks (المعيار العالمي للاستشارات وهندسة البرمجيات)"),
                ("https://toptal.com", "Toptal (الشبكة العالمية لنخبة مهندسي التقنية والحلول المخصصة)"),
                ("https://cleveroad.com", "Cleveroad (استوديو تطوير البرمجيات والحلول الرقمية للشركات)"),
            ]

        # 5. UI/UX & Design Studios
        if any(
            k in site_context_text
            for k in (
                "ui/ux",
                "ux design",
                "product design",
                "design studio",
                "branding agency",
                "graphic design",
                "تصميم واجهات",
                "استوديو تصميم",
                "هوية بصرية",
                "تجربة المستخدم",
            )
        ):
            return [
                ("https://dribbble.com", "Dribbble (المنصة المرجعية العالمية لتصاميم واجهات المستخدم)"),
                ("https://behance.net", "Behance (المرجع القياسي لمعارض الأعمال والهويات البصرية)"),
                ("https://awwwards.com", "Awwwards (المعيار العالمي لتقييم تميز تصميم وتجربة المواقع)"),
            ]

        # 6. Fashion & Apparel E-Commerce
        if any(
            k in site_context_text
            for k in (
                "fashion",
                "clothing",
                "apparel",
                "shoes",
                "sneakers",
                "dress",
                "wear",
                "ملابس",
                "أزياء",
                "موضة",
                "أحذية",
                "عبايات",
                "فساتين",
            )
        ):
            return [
                ("https://www.namshi.com", "Namshi (المنصة الإقليمية الرائدة للأزياء والموضة)"),
                ("https://www.ounass.ae", "Ounass (المنصة الفاخرة للأزياء والعلامات العالمية)"),
                ("https://www.asos.com", "ASOS (المعيار العالمي لتجارة الأزياء العصرية)"),
            ]

        # 7. E-Commerce & Retail Marketplace
        if any(
            k in site_context_text
            for k in (
                "shop",
                "store",
                "market",
                "ecommerce",
                "cart",
                "checkout",
                "noon",
                "amazon",
                "متجر",
                "تسوق",
                "سلة",
                "شراء",
                "منتجات",
                "عروض",
                "تجزئة",
            )
        ):
            return [
                ("https://www.noon.com", "Noon (منصة التجارة الإلكترونية الإقليمية المتكاملة)"),
                ("https://www.amazon.sa", "Amazon SA (المعيار العالمي للتجارة والتسوق الرقمي)"),
                ("https://www.jarir.com", "Jarir (رائد التجزئة والتجارة المتخصصة)"),
            ]

        # 8. Real Estate & Property
        if any(
            k in site_context_text
            for k in (
                "realestate",
                "aqar",
                "property",
                "rent",
                "villas",
                "apartments",
                "عقار",
                "عقارات",
                "إيجار",
                "بيع",
                "شقق",
                "فلل",
                "أراضي",
                "مخططات",
            )
        ):
            return [
                ("https://sa.aqar.fm", "Aqar (المنصة العقارية الرائدة محلياً)"),
                ("https://www.bayut.sa", "Bayut (منصة البحث والاستثمار العقاري)"),
                ("https://www.propertyfinder.sa", "Property Finder (المرجع الإقليمي للعقارات)"),
            ]

        # 9. Travel, Hotels & Flight Booking
        if any(
            k in site_context_text
            for k in (
                "travel",
                "flight",
                "hotel",
                "tour",
                "tourism",
                "airline",
                "سياحة",
                "طيران",
                "فنادق",
                "سفر",
                "حجز",
                "رحلات",
                "عطلات",
            )
        ):
            return [
                ("https://www.almosafer.com", "Almosafer (المنصة الرائدة لحجوزات السفر والسياحة)"),
                ("https://www.booking.com", "Booking (المعيار العالمي لحجوزات الإقامة والفنادق)"),
                ("https://www.flyin.com", "Flyin (المنصة المتكاملة لخدمات الطيران والسياحة)"),
            ]

        # 10. Food Delivery & Restaurants
        if any(
            k in site_context_text
            for k in (
                "food",
                "restaurant",
                "delivery",
                "burger",
                "pizza",
                "chef",
                "مطعم",
                "توصيل",
                "وجبات",
                "طعام",
                "مطبخ",
                "مأكولات",
                "hungerstation",
                "jahez",
            )
        ):
            return [
                ("https://hungerstation.com", "HungerStation (رائد تطبيقات التوصيل والطلب السريع)"),
                ("https://jahez.net", "Jahez (المنصة الرقمية الرائدة لخدمات الأطعمة)"),
                ("https://www.talabat.com", "Talabat (الشبكة الإقليمية لطلب الوجبات)"),
            ]

        # 11. FinTech, Banking & Digital Payments
        if any(
            k in site_context_text
            for k in (
                "fintech",
                "bank",
                "pay",
                "wallet",
                "tamara",
                "tabby",
                "stcpay",
                "مالية",
                "دفع",
                "بنك",
                "تمويل",
                "تقسيط",
                "محفظة رقمية",
                "مدفوعات",
            )
        ):
            return [
                ("https://tamara.co", "Tamara (الرائد في حلول الدفع المرن والتجزئة BNPL)"),
                ("https://tabby.ai", "Tabby (منصة التسوق والمدفوعات الرقمية المرنة)"),
                ("https://stcpay.com.sa", "STC Pay (المحفظة الرقمية المتكاملة للخدمات المالية)"),
            ]

        # 12. Health, Telemedicine & Medical Centers
        if any(
            k in site_context_text
            for k in (
                "health",
                "medical",
                "clinic",
                "doctor",
                "hospital",
                "pharma",
                "صحة",
                "طبي",
                "عيادة",
                "مستشفى",
                "دكتور",
                "صيدلية",
                "رعاية صحية",
                "استشارة طبية",
            )
        ):
            return [
                ("https://www.vezeeta.com", "Vezeeta (المنصة الرقمية للخدمات الطبية وحجز العيادات)"),
                ("https://altibbi.com", "Altibbi (المرجع الطبي والاستشارات الرقمية المعتمدة)"),
                ("https://www.mayoclinic.org", "Mayo Clinic (المعيار العالمي للمعلومات والرعاية الصحية)"),
            ]

        # 13. EdTech, Courses & E-Learning
        if any(
            k in site_context_text
            for k in (
                "academy",
                "course",
                "learn",
                "education",
                "university",
                "school",
                "student",
                "تدريب",
                "أكاديمية",
                "دورات",
                "تعليم",
                "جامعة",
                "طلاب",
                "منهاج",
            )
        ):
            return [
                ("https://academy.hsoub.com", "أكاديمية حسوب (المنصة التعليمية الرائدة للبرمجة وتطوير المهارات)"),
                ("https://coursera.org", "Coursera (المنصة العالمية الرائدة للتعليم والشهادات الاحترافية)"),
                ("https://udemy.com", "Udemy (المنصة المرجعية العالمية للدورات التدريبية المباشرة)"),
            ]

        # 14. News, Journalism & Media
        if any(
            k in site_context_text
            for k in (
                "news",
                "media",
                "press",
                "journal",
                "breaking",
                "إعلام",
                "أخبار",
                "صحافة",
                "جريدة",
                "عاجل",
                "صحيفة",
                "مقال",
            )
        ):
            return [
                ("https://www.aljazeera.net", "AlJazeera (الشبكة الإخبارية الإقليمية)"),
                ("https://www.alarabiya.net", "AlArabiya (المنصة الإخبارية المتكاملة)"),
                ("https://www.asharq.com", "Asharq (منصة الاقتصاد والإعلام المالي)"),
            ]

        # 15. Sports & Live Matches
        if any(
            k in site_context_text
            for k in (
                "sport",
                "bein",
                "kora",
                "stream",
                "goal",
                "match",
                "football",
                "كرة",
                "رياضة",
                "بث",
                "مباراة",
                "دوري",
                "أهداف",
            )
        ):
            return [
                ("https://www.espn.com", "ESPN (المنافس الرياضي والبث العالمي)"),
                ("https://www.yallakora.com", "YallaKora (المنصة الرياضية الإقليمية المباشرة)"),
                ("https://www.kooora.com", "Kooora (المنصة الرياضية الإقليمية الأوسع)"),
            ]

        # 16. Automotive & Car Marketplace
        if any(
            k in site_context_text
            for k in (
                "auto",
                "car",
                "vehicle",
                "motor",
                "dealership",
                "سيارات",
                "سيارة",
                "حراج سيارات",
                "معرض سيارات",
                "قطع غيار",
                "مركبات",
            )
        ):
            return [
                ("https://syarah.com", "Syarah (المنصة الرائدة لبيع وشراء السيارات المعتمدة)"),
                ("https://haraj.com.sa", "Haraj (المنصة الأكبر للإعلانات وسوق المركبات)"),
                ("https://motory.com", "Motory (بوابة السيارات المتخصصة والأسعار)"),
            ]

        # 17. Logistics, Shipping & Delivery
        if any(
            k in site_context_text
            for k in (
                "logistics",
                "shipping",
                "freight",
                "cargo",
                "courier",
                "tracking",
                "شحن",
                "توصيل طرود",
                "لوجستيات",
                "تتبع",
                "نقل بضائع",
            )
        ):
            return [
                ("https://www.aramex.com", "Aramex (الشبكة الإقليمية الرائدة لحلول الشحن والنقل)"),
                ("https://www.smsaexpress.com", "SMSA Express (رائد الخدمات اللوجستية والطرود السريعة)"),
                ("https://splonline.com.sa", "SPL (البريد السعودي وخدمات الشحن الوطنية)"),
            ]

        # 18. Legal, Lawyers & Law Firms
        if any(
            k in site_context_text
            for k in (
                "legal",
                "law",
                "attorney",
                "lawyer",
                "court",
                "justice",
                "قانون",
                "محامي",
                "محاماة",
                "استشارات قانونية",
                "قضية",
                "عدل",
            )
        ):
            return [
                ("https://www.moj.gov.sa", "Najes (بوابة الخدمات العدلية والقانونية الرقمية)"),
                ("https://www.clio.com", "Clio (المعيار التقني العالمي لإدارة مكاتب المحاماة)"),
                ("https://www.lexisnexis.com", "LexisNexis (المرجع العالمي للبحوث والمعلومات القانونية)"),
            ]

        # 19. Cybersecurity & Information Security
        if any(
            k in site_context_text
            for k in (
                "cyber",
                "security",
                "firewall",
                "infosec",
                "pentest",
                "soc",
                "أمن سيبراني",
                "حماية",
                "اختراق",
                "أمن معلومات",
            )
        ):
            return [
                ("https://www.crowdstrike.com", "CrowdStrike (المعيار العالمي للحماية المتقدمة والأمن السيبراني)"),
                ("https://www.paloaltonetworks.com", "Palo Alto Networks (الرائد العالمي في جدران الحماية وشبكات الأمان)"),
                ("https://www.cloudflare.com", "Cloudflare (المنصة العالمية لحماية وتأمين حركة الويب)"),
            ]

        # 20. Cloud Hosting & DevOps
        if any(
            k in site_context_text
            for k in (
                "cloud",
                "hosting",
                "devops",
                "infrastructure",
                "server",
                "vps",
                "استضافة",
                "سحابة",
                "سيرفرات",
                "بنية تحتية",
            )
        ):
            return [
                ("https://aws.amazon.com", "AWS (المعيار السحابي العالمي للبنية التحتية)"),
                ("https://vercel.com", "Vercel (المنصة الرائدة في استضافة وتطوير تطبيقات الويب السحابية)"),
                ("https://www.digitalocean.com", "DigitalOcean (حلول الحوسبة السحابية والاستضافة للمطورين)"),
            ]

        # 21. Recruitment & HR
        if any(
            k in site_context_text
            for k in (
                "job",
                "career",
                "recruitment",
                "hiring",
                "hr",
                "talent",
                "توظيف",
                "وظائف",
                "موارد بشرية",
                "كفاءات",
            )
        ):
            return [
                ("https://www.linkedin.com", "LinkedIn (الشبكة المهنية والتوظيف العالمية الأولى)"),
                ("https://www.bayt.com", "Bayt (منصة الوظائف والتوظيف الإقليمية الرائدة)"),
                ("https://jadarat.sa", "Jadarat (المنصة الوطنية الموحدة للتوظيف)"),
            ]

        # 22. Crypto, Web3 & Blockchain
        if any(
            k in site_context_text
            for k in (
                "crypto",
                "bitcoin",
                "ethereum",
                "blockchain",
                "token",
                "web3",
                "كريبتو",
                "بيتكوين",
                "بلوكتشين",
                "عملات رقمية",
            )
        ):
            return [
                ("https://binance.com", "Binance (المنصة العالمية الرائدة لتداول الأصول الرقمية)"),
                ("https://coinmarketcap.com", "CoinMarketCap (المرجع القياسي لبيانات وأسعار العملات المشفرة)"),
                ("https://ethereum.org", "Ethereum.org (المنصة المرجعية لتطبيقات البلوكتشين والعقود الذكية)"),
            ]

        # 23. Charities & Non-Profit
        if any(
            k in site_context_text
            for k in (
                "charity",
                "donation",
                "ngo",
                "nonprofit",
                "relief",
                "تبرع",
                "خيرية",
                "إغاثة",
                "جمعية خيرية",
                "وقف",
            )
        ):
            return [
                ("https://ehsan.sa", "Ehsan (المنصة الوطنية للعمل الخيري وتوجيه التبرعات)"),
                ("https://shefaa.org.sa", "Shefaa (المنصة الصحية المعتمدة للعلاج والتبرع)"),
                ("https://www.unicef.org", "UNICEF (المرجع الإنساني العالمي للإغاثة ورعاية الطفولة)"),
            ]

        # 24. Entertainment & Video Streaming
        if any(
            k in site_context_text
            for k in (
                "movie",
                "film",
                "series",
                "cinema",
                "streaming",
                "video",
                "أفلام",
                "مسلسلات",
                "سينما",
                "مشاهدة",
                "ترفيه",
            )
        ):
            return [
                ("https://shahid.mbc.net", "Shahid (منصة الترفيه والمشاهدة العربية الأولى)"),
                ("https://www.netflix.com", "Netflix (المعيار العالمي للمحتوى الترفيهي والبث)"),
                ("https://www.osnplus.com", "OSN+ (منصة البث الحصري للإنتاجات العالمية)"),
            ]

        # 25. Gaming & Esports
        if any(
            k in site_context_text
            for k in (
                "game",
                "gaming",
                "esports",
                "playstation",
                "xbox",
                "steam",
                "ألعاب",
                "قيمنق",
                "إلكترونية",
                "بطولات",
            )
        ):
            return [
                ("https://store.steampowered.com", "Steam (المتجر والمجتمع العالمي الأضخم لألعاب الكمبيوتر)"),
                ("https://www.playstation.com", "PlayStation (المعيار القياسي لأجهزة ومنصات الألعاب)"),
                ("https://www.twitch.tv", "Twitch (المنصة الرائدة في البث المباشر للألعاب والرياضات الإلكترونية)"),
            ]

        # 26. Marketing, SEO & Growth
        if any(
            k in site_context_text
            for k in (
                "marketing",
                "seo",
                "growth",
                "advertising",
                "تسويق",
                "تحسين محركات البحث",
                "إعلانات",
                "نمو",
            )
        ):
            return [
                ("https://www.hubspot.com", "HubSpot (المنصة المتكاملة للتسويق وإدارة علاقات العملاء)"),
                ("https://semrush.com", "SEMrush (المرجع القياسي لتحليلات محركات البحث والتسويق الرقمي)"),
                ("https://ahrefs.com", "Ahrefs (المنصة الرائدة لتحليل الروابط وتحسين ظهور المواقع)"),
            ]

        # 27. SaaS Productivity & Project Management
        if any(
            k in site_context_text
            for k in (
                "project management",
                "tasks",
                "workflow",
                "sprint",
                "productivity",
                "kanban",
                "إدارة مشاريع",
                "مهام",
                "إنتاجية",
                "فرق العمل",
            )
        ):
            return [
                ("https://linear.app", "Linear (المعيار العالمي لإدارة المشاريع وسرعة الفرق التقنية)"),
                ("https://notion.so", "Notion (المنصة الرائدة في التوثيق ومساحات العمل الإنتاجية)"),
                ("https://asana.com", "Asana (نظام التنسيق ومتابعة مهام العمل للشركات)"),
            ]

        # 28. Intelligent Regional / Global Digital Benchmark Fallback (Never generic Linear/Stripe/Notion)
        if any(c in site_context_text for c in (".sa", ".ae", ".eg", "riyadh", "jeddah", "dubai", "عربي", "السعودية")):
            return [
                ("https://tamara.co", "Tamara (المنصة الرقمية الرائدة في تجربة المستخدم والتحويل السريع)"),
                ("https://www.noon.com", "Noon (المرجع الإقليمي للمنصات الرقمية وخدمات المستهلك)"),
                ("https://hungerstation.com", "HungerStation (رائد الحلول والتطبيقات الرقمية المباشرة)"),
            ]

        return [
            ("https://github.com", "GitHub (المرجع القياسي للابتكار والحلول الرقمية المتطورة)"),
            ("https://www.producthunt.com", "Product Hunt (المنصة العالمية لاكتشاف وتقييم المنتجات والحلول الرقمية)"),
            ("https://news.ycombinator.com", "Hacker News (المرجع العالمي للتقنية والشركات الرقمية الناشئة)"),
        ]
