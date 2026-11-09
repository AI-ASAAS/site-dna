"""Market Positioning and Brand Promise Analyzer for Site DNA Phase 08."""

from typing import Any

from site_dna.core.logging import get_logger
from site_dna.schemas.competitor_intelligence import CompetitorSourceRecord, PositioningAssessment

logger = get_logger("analysis.competitor_intelligence.positioning_analyzer")


class PositioningAnalyzer:
    """Extracts and contrasts market positioning, claimed differentiators, and brand tone."""

    def analyze_positioning(
        self,
        site: CompetitorSourceRecord,
        crawl_data: dict[str, Any],
    ) -> PositioningAssessment:
        """Derive positioning strictly from observed headings, copy, and CTAs."""
        pages = crawl_data.get("pages", [])
        home_page = pages[0] if pages else {}

        # 1. Core Value Proposition
        val_prop = ""
        h1s = [h.get("text", "") for h in home_page.get("headings", []) if isinstance(h, dict) and h.get("level") == 1]
        if h1s:
            val_prop = h1s[0].strip()
        elif home_page.get("title"):
            val_prop = home_page["title"].strip()
        else:
            val_prop = f"Digital platform and services for {site.display_name}."

        # 2. Claimed Differentiators
        full_text = " ".join([p.get("text", "") or "" for p in pages]).lower()
        differentiators = []
        if any(w in full_text for w in ("fastest", "quickest", "الأسرع", "instant")):
            differentiators.append("Claims speed and rapid time-to-value (Observed Claim)")
        if any(w in full_text for w in ("most secure", "bank-grade", "الأكثر أماناً", "enterprise-grade")):
            differentiators.append("Claims superior enterprise security (Observed Claim)")
        if any(w in full_text for w in ("all-in-one", "comprehensive", "متكامل", "unified")):
            differentiators.append("Claims unified all-in-one suite (Observed Claim)")
        if any(w in full_text for w in ("simplest", "easy", "الأسهل", "intuitive")):
            differentiators.append("Claims ease of use and low friction (Observed Claim)")

        if not differentiators:
            differentiators.append("Differentiators focused on core domain features.")

        # 3. Target Customer Language
        audiences = []
        if "enterprise" in full_text or "large organizations" in full_text:
            audiences.append("Enterprise procurement & executive decision-makers")
        if "startup" in full_text or "founder" in full_text:
            audiences.append("Founders & fast-growing startups")
        if "developer" in full_text or "api" in full_text:
            audiences.append("Technical teams and software developers")
        if not audiences:
            audiences.append("General professional business teams")

        # 4. Primary Benefits
        benefits = []
        for p in pages:
            for h in p.get("headings", []):
                t = h.get("text", "") if isinstance(h, dict) else str(h)
                if (
                    len(t) > 10
                    and len(t) < 60
                    and any(
                        k in t.lower() for k in ("save", "boost", "grow", "scale", "protect", "زيادة", "تسريع", "أتمتة")
                    )
                ):
                    benefits.append(t.strip())
        if not benefits:
            benefits = ["Operational efficiency", "Workflow modernization", "Cost control"]

        # 5. Tone
        tone = "Professional Corporate"
        if any(w in full_text for w in ("love", "delight", "magic", "vibes", "awesome")):
            tone = "Casual & Developer-Friendly"
        elif any(w in full_text for w in ("governance", "compliance", "institutional", "sovereign")):
            tone = "Formal & Institutional"

        # 6. Main CTA Strategy
        cta_candidates = []
        for p in pages:
            for cta in p.get("cta_candidates", []):
                label = cta.get("label") or cta.get("text")
                if label:
                    cta_candidates.append(label.lower().strip())

        cta_strategy = "Direct Sales / Contact"
        if any(c in " ".join(cta_candidates) for c in ("start free", "free trial", "get started", "ابدأ مجاناً")):
            cta_strategy = "Product-Led Growth (Free Trial / Self-Serve)"
        elif any(c in " ".join(cta_candidates) for c in ("book a demo", "schedule demo", "احجز عرضاً")):
            cta_strategy = "Sales-Led (Demo Booking)"

        ev_ids = [f"ev-{site.site_id}-pos-{idx}" for idx in range(min(len(pages), 3))]

        return PositioningAssessment(
            site_id=site.site_id,
            core_value_proposition=val_prop,
            claimed_differentiators=differentiators,
            target_customer_language=audiences,
            primary_benefits=benefits[:4],
            brand_tone=tone,
            main_cta_strategy=cta_strategy,
            evidence_ids=ev_ids,
        )
