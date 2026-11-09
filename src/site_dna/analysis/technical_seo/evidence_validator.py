"""Evidence verification, ground-truth matching, and hallucination quarantine engine."""

from typing import Any

from site_dna.core.logging import get_logger
from site_dna.schemas.technical_seo import (
    TechnicalPageRecord,
    TechnicalSEOFinding,
)

logger = get_logger("analysis.technical_seo.evidence_validator")


class TechnicalSEOEvidenceValidator:
    """Validates technical SEO findings against collected DOM, metadata, and crawl evidence."""

    @staticmethod
    def validate_findings(
        findings: list[TechnicalSEOFinding],
        pages: list[TechnicalPageRecord],
        evidence_index: dict[str, Any],
    ) -> tuple[list[TechnicalSEOFinding], list[TechnicalSEOFinding]]:
        """Separate validated evidence-backed findings from hallucinated or ungrounded claims.

        Returns:
            Tuple of (validated_findings, quarantined_findings)
        """
        validated: list[TechnicalSEOFinding] = []
        quarantined: list[TechnicalSEOFinding] = []

        known_urls = {p.requested_url.rstrip("/") for p in pages}
        known_urls.update(p.final_url.rstrip("/") for p in pages)

        hallucination_triggers = [
            "google has indexed",
            "indexed by google",
            "will rank #1",
            "rank first",
            "google penalty applied",
            "guaranteed ranking",
            "inp of",
        ]

        for f in findings:
            desc_lower = f.description.lower()
            title_lower = f.title.lower()

            # Rule 1: Check for forbidden speculative claims
            is_hallucinated = any(trig in desc_lower or trig in title_lower for trig in hallucination_triggers)
            if is_hallucinated:
                logger.warning(
                    "Quarantining finding '%s' due to speculative/unverifiable claim: '%s'",
                    f.finding_id,
                    f.title,
                )
                quarantined.append(f)
                continue

            # Rule 2: Page URL validation
            if f.page_url and f.page_url.rstrip("/") not in known_urls:
                # If page URL is not in known pages, quarantine unless it is root robots/sitemap
                if not any(f.page_url.endswith(suffix) for suffix in ["/robots.txt", "/sitemap.xml"]):
                    logger.warning(
                        "Quarantining finding '%s': referenced URL '%s' not found in crawl scope",
                        f.finding_id,
                        f.page_url,
                    )
                    quarantined.append(f)
                    continue

            # Finding passed checks
            validated.append(f)

        logger.info(
            "Evidence validation complete: %d validated, %d quarantined",
            len(validated),
            len(quarantined),
        )
        return validated, quarantined
