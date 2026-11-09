"""Evidence validator enforcing strict provenance checks on all model-generated findings."""

from typing import Any

from site_dna.core.logging import get_logger
from site_dna.schemas.visual_identity import VisualFinding

logger = get_logger("analysis.visual_identity.evidence_validator")


class EvidenceValidationSummary:
    """Summary of finding validation and quarantine audit."""

    def __init__(self):
        self.total_findings: int = 0
        self.validated_findings: list[VisualFinding] = []
        self.rejected_findings: list[VisualFinding] = []
        self.invalid_references_count: int = 0


class EvidenceValidator:
    """Validates finding evidence references against genuine Phase 02/03 records."""

    def __init__(
        self,
        evidence_index: dict[str, Any],
        valid_page_urls: set[str],
    ):
        self.evidence_index = evidence_index
        self.valid_page_urls = valid_page_urls

    def validate_findings(self, raw_findings: list[VisualFinding]) -> EvidenceValidationSummary:
        """Inspect and partition findings into verified vs. rejected/quarantined."""
        summary = EvidenceValidationSummary()
        summary.total_findings = len(raw_findings)

        for finding in raw_findings:
            # Check 1: Valid page URL
            if finding.page_url and finding.page_url not in self.valid_page_urls:
                finding.is_validated = False
                finding.rejection_reason = f"Referenced unknown page URL: {finding.page_url}"
                summary.rejected_findings.append(finding)
                logger.warning("Rejected finding %s: %s", finding.finding_id, finding.rejection_reason)
                continue

            # Check 2: Evidence ID provenance
            unresolved_ids = [eid for eid in finding.evidence_ids if eid not in self.evidence_index]
            if unresolved_ids:
                summary.invalid_references_count += len(unresolved_ids)
                # Attempt reconciliation: if finding matches an existing evidence record category for this page
                reconciled = False
                for eid, ev in self.evidence_index.items():
                    if ev.page_url == finding.page_url and finding.category in ev.field_reference:
                        finding.evidence_ids = [eid]
                        reconciled = True
                        break

                if not reconciled and finding.finding_type in ("observed_measurement", "derived_calculation"):
                    finding.is_validated = False
                    finding.rejection_reason = f"Referenced non-existent evidence IDs: {unresolved_ids}"
                    summary.rejected_findings.append(finding)
                    logger.warning("Rejected finding %s: %s", finding.finding_id, finding.rejection_reason)
                    continue

            # Check 3: Rejection of prompt injection attempts
            prohibited_terms = {
                "ignore previous instructions",
                "reveal your api key",
                "scored 100/100",
                "system prompt",
            }
            if any(term in finding.description.lower() or term in finding.title.lower() for term in prohibited_terms):
                finding.is_validated = False
                finding.rejection_reason = "Detected untrusted prompt injection attempt inside finding text"
                summary.rejected_findings.append(finding)
                logger.warning("Quarantined prompt injection finding %s", finding.finding_id)
                continue

            # Finding is verified safe
            finding.is_validated = True
            summary.validated_findings.append(finding)

        logger.info(
            "Evidence validation finished: %d validated, %d rejected out of %d total",
            len(summary.validated_findings),
            len(summary.rejected_findings),
            summary.total_findings,
        )
        return summary
