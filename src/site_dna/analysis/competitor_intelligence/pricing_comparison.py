"""Pricing Comparison and Normalization Engine for Site DNA Phase 08."""

import re
from datetime import datetime, timezone
from typing import Any

from site_dna.core.logging import get_logger
from site_dna.schemas.competitor_intelligence import CompetitorSourceRecord, PricingRecord

logger = get_logger("analysis.competitor_intelligence.pricing_comparison")


class PricingComparator:
    """Extracts public pricing tiers and enforces strict comparability safeguards."""

    def compare_pricing(
        self,
        primary_site: CompetitorSourceRecord,
        competitor_sites: list[CompetitorSourceRecord],
        crawl_dataset: dict[str, dict[str, Any]],
    ) -> list[PricingRecord]:
        """Extract and evaluate pricing models across all benchmarked sites."""
        pricing_records: list[PricingRecord] = []
        all_sites = [primary_site] + competitor_sites

        for site in all_sites:
            data = crawl_dataset.get(site.site_id, {})
            records = self._extract_site_pricing(site, data)
            pricing_records.extend(records)

        # Cross-evaluate comparability across extracted plans
        self._evaluate_comparability(pricing_records)
        return pricing_records

    def _extract_site_pricing(
        self,
        site: CompetitorSourceRecord,
        data: dict[str, Any],
    ) -> list[PricingRecord]:
        """Extract pricing information from crawled pages."""
        pages = data.get("pages", [])
        pricing_page = next(
            (p for p in pages if "pricing" in p.get("url", "").lower() or "price" in (p.get("title") or "").lower()),
            None,
        )
        now_iso = datetime.now(timezone.utc).isoformat()

        if not pricing_page:
            # Check if any page mentions contact sales
            full_text = " ".join([p.get("text", "") or "" for p in pages]).lower()
            if "contact sales" in full_text or "request a quote" in full_text or "تواصل مع المبيعات" in full_text:
                return [
                    PricingRecord(
                        plan_id=f"prc-{site.site_id}-quote",
                        site_id=site.site_id,
                        plan_name="Custom / Enterprise",
                        amount=None,
                        currency=None,
                        billing_interval="contact_sales",
                        unit_basis="unknown",
                        is_contact_sales=True,
                        comparability_status="contact_sales",
                        source_url=site.url,
                        observation_date=now_iso,
                        notes="No numerical prices published; site directs users to contact sales for custom pricing.",
                    )
                ]
            return [
                PricingRecord(
                    plan_id=f"prc-{site.site_id}-none",
                    site_id=site.site_id,
                    plan_name="Unpublished Pricing",
                    amount=None,
                    currency=None,
                    billing_interval=None,
                    unit_basis=None,
                    is_contact_sales=False,
                    comparability_status="not_published",
                    source_url=site.url,
                    observation_date=now_iso,
                    notes=f"No public pricing structure found in the {len(pages)} collected pages.",
                )
            ]

        # Pricing page found: look for numbers, currencies, intervals
        p_text = (pricing_page.get("text", "") or "") + " " + (pricing_page.get("raw_html", "") or "")
        source_url = pricing_page.get("url", site.url)

        # Match currency symbols and figures like $49, 150 SAR, 200 USD
        price_matches = re.findall(
            r"(?:(\$|USD|SAR|EUR|ريال)\s*([0-9]{1,4}))|(?:([0-9]{1,4})\s*(\$|USD|SAR|EUR|ريال))", p_text
        )

        plans: list[PricingRecord] = []
        if price_matches:
            for idx, match in enumerate(price_matches[:3], start=1):
                curr = match[0] or match[3]
                amt_str = match[1] or match[2]
                try:
                    amt = float(amt_str)
                    interval = "annual" if "annual" in p_text.lower() or "year" in p_text.lower() else "monthly"
                    unit = "per_user" if "user" in p_text.lower() or "seat" in p_text.lower() else "flat"

                    plans.append(
                        PricingRecord(
                            plan_id=f"prc-{site.site_id}-tier-{idx}",
                            site_id=site.site_id,
                            plan_name=f"Tier {idx}",
                            amount=amt,
                            currency=curr.upper() if len(curr) == 3 else curr,
                            billing_interval=interval,
                            unit_basis=unit,
                            is_contact_sales=False,
                            comparability_status="comparable",
                            source_url=source_url,
                            observation_date=now_iso,
                            notes=f"Observed published price of {amt} {curr} ({interval}).",
                        )
                    )
                except Exception:
                    continue

        if not plans:
            # Pricing page exists but offers custom quotes
            plans.append(
                PricingRecord(
                    plan_id=f"prc-{site.site_id}-quote",
                    site_id=site.site_id,
                    plan_name="Contact Sales Tier",
                    amount=None,
                    currency=None,
                    billing_interval="contact_sales",
                    unit_basis="unknown",
                    is_contact_sales=True,
                    comparability_status="contact_sales",
                    source_url=source_url,
                    observation_date=now_iso,
                    notes="Pricing page exists but lists 'Contact Sales' without published numbers.",
                )
            )

        return plans

    def _evaluate_comparability(self, records: list[PricingRecord]) -> None:
        """Mark plans as not_comparable if currencies or billing intervals differ without rate conversion."""
        currencies = {r.currency for r in records if r.currency}
        intervals = {
            r.billing_interval for r in records if r.billing_interval and r.billing_interval != "contact_sales"
        }

        if len(currencies) > 1 or len(intervals) > 1:
            for r in records:
                if r.amount is not None:
                    r.comparability_status = "not_comparable"
                    r.notes += " Marked NOT_COMPARABLE due to divergent currencies or billing intervals across competitors without live FX normalization."
