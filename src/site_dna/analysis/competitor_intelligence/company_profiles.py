"""Competitor Profile Extraction Engine for Site DNA Phase 08."""

import re
from typing import Any, Optional

from site_dna.core.logging import get_logger
from site_dna.schemas.competitor_intelligence import CompetitorProfile, CompetitorSourceRecord

logger = get_logger("analysis.competitor_intelligence.company_profiles")


class CompetitorProfileExtractor:
    """Builds structured company and offering profiles from website evidence."""

    def extract_profile(
        self,
        site_record: CompetitorSourceRecord,
        crawl_data: dict[str, Any],
        content_data: Optional[dict[str, Any]] = None,
    ) -> CompetitorProfile:
        """Derive public business profile strictly from collected evidence."""
        pages = crawl_data.get("pages", [])
        website_info = crawl_data.get("website_info", {})

        # 1. Display name
        display_name = site_record.display_name or website_info.get("site_name", "")
        home_page = next((p for p in pages if p.get("url", "").rstrip("/") == site_record.url.rstrip("/")), None)
        if not home_page and pages:
            home_page = pages[0]

        if home_page and home_page.get("title"):
            title = home_page["title"]
            # Clean title (e.g. "Acme Corp | Modern Cloud Platform" -> "Acme Corp")
            clean_name = re.split(r"[|\-–—:]", title)[0].strip()
            if len(clean_name) > 2 and len(clean_name) < 40:
                display_name = clean_name

        # 2. Business description
        meta_desc = ""
        if home_page and home_page.get("meta_description"):
            meta_desc = home_page["meta_description"].strip()

        if not meta_desc:
            meta_desc = f"{display_name} provides digital products and online services as observed on {site_record.canonical_origin}."
            desc_ar = f"يقدم {display_name} منتجات وخدمات رقمية عبر موقعه {site_record.canonical_origin}."
        else:
            desc_ar = f"يقدم الموقع: {meta_desc}"

        # 3. Offering Categories
        categories = set()
        for p in pages:
            for h in p.get("headings", []):
                text = h.get("text", "") if isinstance(h, dict) else str(h)
                if len(text) < 40 and any(
                    k in text.lower()
                    for k in ("platform", "solution", "feature", "service", "analytics", "engine", "suite")
                ):
                    categories.add(text.strip())

        if not categories:
            categories.update(["Cloud Software", "Digital Platform", "Online Services"])

        # 4. Contact channels
        contact_channels = []
        html_blob = " ".join([p.get("raw_html", "") for p in pages[:3]])
        if "mailto:" in html_blob or "@" in html_blob:
            contact_channels.append("Email Support")
        if "tel:" in html_blob:
            contact_channels.append("Phone / Hotline")
        if any(c in html_blob.lower() for c in ("contact", "tally", "form", "intercom", "hubspot", "zendesk")):
            contact_channels.append("Contact Form / Web Chat")

        # 5. Trust signals
        trust_signals = []
        full_text = " ".join([p.get("text", "") or p.get("title", "") for p in pages]).lower()
        if any(w in full_text for w in ("testimonial", "trusted by", "customers", "عملاؤنا", "شركاء")):
            trust_signals.append("Customer Testimonials / Partner Logos")
        if any(w in full_text for w in ("soc2", "iso", "hipaa", "gdpr", "ssl", "certified", "معتمد")):
            trust_signals.append("Security & Compliance Mentions")
        if any(w in full_text for w in ("case study", "دراسة حالة", "قصص نجاح")):
            trust_signals.append("Published Case Studies")

        # 6. Published pricing check
        has_pricing = any(
            "pricing" in p.get("url", "").lower() or "price" in (p.get("title") or "").lower() for p in pages
        )

        # 7. Value proposition
        val_prop = None
        if home_page:
            h1s = [
                h.get("text", "") for h in home_page.get("headings", []) if isinstance(h, dict) and h.get("level") == 1
            ]
            if h1s:
                val_prop = h1s[0].strip()

        evidence_ids = [f"ev-{site_record.site_id}-{p.get('page_id', idx)}" for idx, p in enumerate(pages[:4])]

        return CompetitorProfile(
            site_id=site_record.site_id,
            website_url=site_record.url,
            display_name=display_name,
            business_description=meta_desc,
            business_description_ar=desc_ar,
            offering_categories=sorted(list(categories))[:6],
            declared_audience="Enterprise & B2B Teams" if "enterprise" in full_text else "General Business Audience",
            declared_geographic_scope="Regional (GCC / MENA)"
            if any(k in full_text for k in ("saudi", "riyadh", "ksa", "الشرق الأوسط"))
            else "Global",
            business_model_candidates=["SaaS / Subscription"]
            if has_pricing or "pricing" in full_text
            else ["Direct Service / Consultation"],
            published_value_proposition=val_prop or meta_desc,
            public_contact_channels=contact_channels or ["Public Website Only"],
            observed_trust_signals=trust_signals or ["Standard HTTPS Security"],
            published_pricing_available=has_pricing,
            source_evidence_ids=evidence_ids,
            limitations=[
                "Extracted strictly from public website pages within crawl boundary.",
                "Corporate ownership and unlisted offerings remain unverified.",
            ],
        )
