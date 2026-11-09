"""Competitor Relevance Classification and Comparability Engine for Site DNA."""

import re
from typing import Any, Optional

from site_dna.core.logging import get_logger
from site_dna.schemas.competitor_intelligence import CompetitorRelevance, CompetitorSourceRecord, RelevanceCategory

logger = get_logger("analysis.competitor_intelligence.relevance")


class CompetitorRelevanceClassifier:
    """Evaluates whether a competitor is direct, indirect, adjacent, or non-comparable."""

    def classify_relevance(
        self,
        primary_site: CompetitorSourceRecord,
        competitor_site: CompetitorSourceRecord,
        primary_data: dict[str, Any],
        competitor_data: dict[str, Any],
        user_retained_exploratory: bool = False,
    ) -> CompetitorRelevance:
        """Analyze offering overlap, audience alignment, and business models."""
        primary_categories = self._extract_categories(primary_data)
        competitor_categories = self._extract_categories(competitor_data)

        # 1. Category Overlap
        common = set(c.lower() for c in primary_categories).intersection(set(c.lower() for c in competitor_categories))

        # 2. Keywords in headings/titles
        p_text = self._aggregate_text(primary_data).lower()
        c_text = self._aggregate_text(competitor_data).lower()

        # Shared industry terms
        industry_keywords = [
            "saas",
            "software",
            "api",
            "platform",
            "cloud",
            "analytics",
            "marketing",
            "crm",
            "sales",
            "ecommerce",
            "ai",
            "security",
            "b2b",
            "consulting",
            "design",
            "development",
            "financial",
            "education",
            "healthcare",
        ]
        shared_keywords = [kw for kw in industry_keywords if kw in p_text and kw in c_text]

        # 3. Compute score and category
        if common or (len(shared_keywords) >= 2):
            category: RelevanceCategory = "direct"
            score = 85.0 + min(len(common) * 5.0, 15.0)
            reason = f"Direct competitor sharing core service categories: {', '.join(common or shared_keywords)}."
            reason_ar = f"منافس مباشر يتطابق في فئات الخدمات الأساسية: {', '.join(common or shared_keywords)}."
        elif shared_keywords:
            category = "indirect"
            score = 65.0
            reason = (
                f"Indirect competitor operating in adjacent domain with shared focus: {', '.join(shared_keywords)}."
            )
            reason_ar = f"منافس غير مباشر ينشط في مجال مجاور ويشترك في محاور: {', '.join(shared_keywords)}."
        elif not competitor_data or not competitor_data.get("pages"):
            category = "unknown"
            score = 40.0
            reason = "Insufficient website evidence collected to establish definitive competitive relevance."
            reason_ar = "الأدلة المجموعة من الموقع غير كافية لتحديد درجة التنافسية بدقة."
        else:
            category = "adjacent" if user_retained_exploratory else "not_comparable"
            score = 30.0
            reason = (
                "Low offering overlap observed in collected pages; retained for exploratory benchmark."
                if user_retained_exploratory
                else "Substantially different business domain or service scope."
            )
            reason_ar = (
                "تداخل محدود في الخدمات؛ تم الإبقاء عليه لأغراض الفحص الاستكشافي."
                if user_retained_exploratory
                else "نطاق عمل مختلف جوهرياً عن الموقع المستهدف."
            )

        return CompetitorRelevance(
            site_id=competitor_site.site_id,
            url=competitor_site.url,
            relevance_category=category,
            relevance_score=round(score, 1),
            reason=reason,
            reason_ar=reason_ar,
            observed_categories=competitor_categories,
            declared_audience=self._extract_audience(competitor_data),
            declared_geography=self._extract_geography(competitor_data),
            user_retained_exploratory=user_retained_exploratory,
        )

    def _extract_categories(self, data: dict[str, Any]) -> list[str]:
        """Extract observed business categories from crawl pages."""
        categories = set()
        pages = data.get("pages", [])
        for p in pages:
            url_lower = p.get("url", "").lower()
            title_lower = (p.get("title") or "").lower()
            for part in re.split(r"[/_\-\s]+", url_lower + " " + title_lower):
                if len(part) > 3 and part in (
                    "features",
                    "pricing",
                    "solutions",
                    "services",
                    "products",
                    "platform",
                    "security",
                    "analytics",
                    "integrations",
                    "ai",
                    "automation",
                    "marketing",
                    "developer",
                    "enterprise",
                ):
                    categories.add(part.capitalize())
        return sorted(list(categories))

    def _aggregate_text(self, data: dict[str, Any]) -> str:
        """Combine visible titles and headings."""
        texts = []
        for p in data.get("pages", []):
            if p.get("title"):
                texts.append(p["title"])
            for h in p.get("headings", []):
                if isinstance(h, dict) and h.get("text"):
                    texts.append(h["text"])
        return " ".join(texts)

    def _extract_audience(self, data: dict[str, Any]) -> Optional[str]:
        """Detect explicitly declared target audience."""
        text = self._aggregate_text(data).lower()
        if "enterprise" in text:
            return "Enterprise & Large Teams"
        if "startups" in text or "small business" in text or "smb" in text:
            return "Startups & Small-to-Medium Businesses"
        if "developers" in text or "engineers" in text:
            return "Developers & Technical Teams"
        return "General Business / B2B"

    def _extract_geography(self, data: dict[str, Any]) -> Optional[str]:
        """Detect declared geographic service focus."""
        text = self._aggregate_text(data).lower()
        if "saudi" in text or "riyadh" in text or "ksa" in text or "السعودية" in text:
            return "Saudi Arabia / GCC"
        if "middle east" in text or "mena" in text or "الشرق الأوسط" in text:
            return "MENA Region"
        return "Global / Unrestricted"
