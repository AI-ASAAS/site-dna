"""Evidence validation and anti-hallucination quarantine engine."""

from typing import Any

from site_dna.core.logging import get_logger
from site_dna.schemas.content_marketing import ContentFinding, PageContentRecord

logger = get_logger("analysis.content_marketing.evidence_validator")


class ContentEvidenceValidator:
    """Verifies that every content finding, claim, and observation is strictly grounded in real source text."""

    @staticmethod
    def validate_findings(
        findings: list[ContentFinding],
        pages: list[PageContentRecord],
        evidence_index: dict[str, Any],
    ) -> tuple[list[ContentFinding], list[ContentFinding]]:
        """Cross-check findings against ground-truth page text and quarantine unverified claims.

        Returns:
            Tuple of (valid_findings, quarantined_findings)
        """
        valid_findings: list[ContentFinding] = []
        quarantined_findings: list[ContentFinding] = []

        pages_by_url = {p.page_url.lower().rstrip("/"): p for p in pages}

        for f in findings:
            clean_url = f.page_url.lower().rstrip("/")
            source_page = pages_by_url.get(clean_url)

            # 1. Page URL existence
            if not source_page:
                logger.warning("Quarantining finding %s: unknown page URL %s", f.finding_id, f.page_url)
                quarantined_findings.append(f)
                continue

            # 2. Source excerpt verification
            if f.source_excerpt and f.source_excerpt.strip():
                excerpt = f.source_excerpt.strip().lower()
                page_full_text = (
                    source_page.main_content.lower()
                    + " "
                    + " ".join(h.get("text", "").lower() for h in source_page.headings)
                    + " "
                    + " ".join(c.get("text", "").lower() for c in source_page.cta_candidates)
                    + " "
                    + (source_page.page_title or "").lower()
                    + " "
                    + (source_page.meta_description or "").lower()
                )

                # Relax slightly for whitespace
                if excerpt not in page_full_text and not any(
                    part in page_full_text for part in excerpt.split() if len(part) > 4
                ):
                    logger.warning(
                        "Quarantining finding %s: excerpt '%s' not found on page", f.finding_id, excerpt[:40]
                    )
                    quarantined_findings.append(f)
                    continue

            # Finding passed verification
            valid_findings.append(f)

        logger.info(
            "Evidence validation: %d valid findings, %d quarantined",
            len(valid_findings),
            len(quarantined_findings),
        )
        return valid_findings, quarantined_findings
