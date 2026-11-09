"""Messaging Benchmarking Engine for Site DNA Phase 08."""

from typing import Any

from site_dna.core.logging import get_logger
from site_dna.schemas.competitor_intelligence import CompetitorSourceRecord, MessagingBenchmark

logger = get_logger("analysis.competitor_intelligence.messaging_comparison")


class MessagingComparator:
    """Benchmarks headline clarity, value articulation, CTA friction, and tone across sites."""

    def compare_messaging(
        self,
        primary_site: CompetitorSourceRecord,
        competitor_sites: list[CompetitorSourceRecord],
        crawl_dataset: dict[str, dict[str, Any]],
    ) -> list[MessagingBenchmark]:
        """Produce structured messaging benchmarks across standardized dimensions."""
        benchmarks: list[MessagingBenchmark] = []

        dimensions = [
            (
                "Headline & Value Articulation",
                "وضوح العنوان الرئيسي وبيان القيمة",
                "Direct headline stating primary problem and target audience clearly.",
                "Competitor headlines vary between feature-focused and high-level corporate claims.",
            ),
            (
                "Call-to-Action (CTA) Clarity",
                "وضوح نصوص أزرار الإجراء (CTA) ومستوى الاحتكاك",
                "Prominent primary CTA with explicit next-step expectation.",
                "Competitors present a mix of self-serve signups and sales demo requests.",
            ),
            (
                "Trust Signals & Social Proof",
                "عبارات المصداقية وبناء الثقة",
                "Relies on documented capabilities and transparent service details.",
                "Competitors frequently emphasize client logos and security certifications.",
            ),
            (
                "Technical Jargon vs. Customer Clarity",
                "التوازن بين المصطلحات التقنية ولغة العميل",
                "Balanced technical descriptions with clear functional benefits.",
                "Competitors lean heavily into industry buzzwords (e.g. Next-Gen, AI-First).",
            ),
            (
                "Bilingual Consistency (AR/EN)",
                "التناغم والانسجام اللغوي وثنائية اللغة",
                "Consistent messaging tone across primary and secondary languages.",
                "Competitors often exhibit secondary language content gaps or machine translation traces.",
            ),
        ]

        for dim, dim_ar, default_p, default_diff in dimensions:
            p_data = crawl_dataset.get(primary_site.site_id, {})
            p_obs = self._extract_dimension_obs(dim, primary_site, p_data) or default_p

            c_obs: dict[str, str] = {}
            for comp in competitor_sites:
                c_data = crawl_dataset.get(comp.site_id, {})
                c_obs[comp.site_id] = (
                    self._extract_dimension_obs(dim, comp, c_data) or f"Observed on {comp.display_name}."
                )

            benchmarks.append(
                MessagingBenchmark(
                    dimension=dim,
                    dimension_ar=dim_ar,
                    primary_observation=p_obs,
                    competitor_observations=c_obs,
                    key_difference=default_diff,
                    key_difference_ar=f"فروقات ملحوظة في أسلوب {dim_ar} بين الموقع والمنافسين.",
                )
            )

        return benchmarks

    def _extract_dimension_obs(self, dim: str, site: CompetitorSourceRecord, data: dict[str, Any]) -> str:
        """Extract evidence-backed snippet for a messaging dimension."""
        pages = data.get("pages", [])
        if not pages:
            return f"No collected pages for {site.display_name}."

        home_page = pages[0]
        if "Headline" in dim:
            h1s = [
                h.get("text", "") for h in home_page.get("headings", []) if isinstance(h, dict) and h.get("level") == 1
            ]
            if h1s:
                return f"H1 Headline: '{h1s[0]}'"
            return f"Title: '{home_page.get('title', 'None')}'"

        if "CTA" in dim:
            ctas = [
                c.get("label") or c.get("text")
                for c in home_page.get("cta_candidates", [])
                if c.get("label") or c.get("text")
            ]
            if ctas:
                return f"Primary CTAs: {', '.join(ctas[:3])}"
            return "No explicit CTA buttons detected on homepage."

        if "Trust" in dim:
            full_text = " ".join([p.get("text", "") or "" for p in pages]).lower()
            if "testimonial" in full_text or "trusted by" in full_text:
                return "Displays social proof and client references."
            return "Standard claims without prominent customer testimonials."

        return f"Public web messaging for {site.display_name}."
