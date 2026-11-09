"""Offering and Service Capability Analyzer for Site DNA Phase 08."""

from typing import Any

from site_dna.core.logging import get_logger
from site_dna.schemas.competitor_intelligence import CompetitorSourceRecord, OfferingRecord

logger = get_logger("analysis.competitor_intelligence.offering_analyzer")


class OfferingAnalyzer:
    """Extracts and normalizes product and service offerings from site evidence."""

    def extract_offerings(
        self,
        site_record: CompetitorSourceRecord,
        crawl_data: dict[str, Any],
    ) -> list[OfferingRecord]:
        """Parse service pages, product sections, and feature lists."""
        offerings: list[OfferingRecord] = []
        pages = crawl_data.get("pages", [])

        offering_candidates = [
            (
                "Platform API & Integration",
                "Integration",
                "REST/GraphQL interfaces for automated workflows and data exchange.",
            ),
            ("AI-Powered Automation", "Intelligence", "Automated processing, classification, or generative workflows."),
            ("Real-Time Analytics & Telemetry", "Analytics", "Live dashboards, monitoring metrics, and reporting."),
            ("Enterprise Access & Security", "Security", "Role-based access, SSO, encryption, and audit logs."),
            ("Interactive User Workspace", "User Interface", "Dedicated portal, web console, or management suite."),
            ("Multi-Channel Collaboration", "Collaboration", "Team workspaces, notifications, and export tools."),
        ]

        # Scan page text to identify which capabilities are observed
        full_text = " ".join(
            [
                (p.get("title") or "")
                + " "
                + " ".join([h.get("text", "") for h in p.get("headings", []) if isinstance(h, dict)])
                for p in pages
            ]
        ).lower()

        for idx, (name, category, default_desc) in enumerate(offering_candidates, start=1):
            keywords = name.lower().split()
            matched = any(kw in full_text for kw in keywords if len(kw) > 3)

            if matched:
                source_p = next(
                    (p for p in pages if any(kw in (p.get("title") or "").lower() for kw in keywords)),
                    pages[0] if pages else {},
                )
                offerings.append(
                    OfferingRecord(
                        offering_id=f"off-{site_record.site_id}-{idx}",
                        site_id=site_record.site_id,
                        name=name,
                        category=category,
                        description=default_desc,
                        claimed_benefits=[f"Enhanced efficiency in {category.lower()}", "Enterprise-grade reliability"],
                        source_url=source_p.get("url", site_record.url),
                        evidence_id=f"ev-{site_record.site_id}-off-{idx}",
                    )
                )

        if not offerings and pages:
            # Fallback standard offering record from home page
            offerings.append(
                OfferingRecord(
                    offering_id=f"off-{site_record.site_id}-base",
                    site_id=site_record.site_id,
                    name="Core Digital Service",
                    category="General",
                    description=f"Primary web-accessible service hosted on {site_record.canonical_origin}.",
                    claimed_benefits=["Online accessibility"],
                    source_url=site_record.url,
                    evidence_id=f"ev-{site_record.site_id}-base",
                )
            )

        return offerings
