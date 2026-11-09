"""Evidence Provenance and Anti-Hallucination Validator for Site DNA Phase 10."""

from site_dna.core.logging import get_logger
from site_dna.schemas.accessibility import AccessibilityFinding

logger = get_logger("analysis.accessibility.evidence_validator")

PROHIBITED_FABRICATIONS = [
    "screen reader cannot read",
    "screen reader fails",
    "this website is wcag aa compliant",
    "fully certified wcag",
    "keyboard users are trapped",
]


class AccessibilityEvidenceValidator:
    """Enforces evidence provenance and filters out hallucinated or unsupported accessibility claims."""

    def validate_findings(
        self,
        findings: list[AccessibilityFinding],
        known_evidence_ids: set[str],
    ) -> tuple[list[AccessibilityFinding], list[AccessibilityFinding]]:
        """Validate findings against registered evidence IDs and hallucination rules."""
        validated: list[AccessibilityFinding] = []
        rejected: list[AccessibilityFinding] = []

        for f in findings:
            desc_lower = f.description.lower()
            title_lower = f.title.lower()

            # 1. Check for prohibited absolute claims
            if any(p in desc_lower or p in title_lower for p in PROHIBITED_FABRICATIONS):
                logger.warning("Rejected finding due to ungrounded absolute claim: %s", f.finding_id)
                rejected.append(f)
                continue

            # 2. Check for missing evidence IDs
            if not f.evidence_ids:
                logger.warning("Rejected finding due to missing evidence IDs: %s", f.finding_id)
                rejected.append(f)
                continue

            # 3. Check evidence ID provenance
            has_valid_evidence = False
            for ev_id in f.evidence_ids:
                if ev_id in known_evidence_ids:
                    has_valid_evidence = True
                    break

            if not has_valid_evidence:
                logger.warning("Rejected finding with ungrounded evidence IDs: %s (%s)", f.finding_id, f.evidence_ids)
                rejected.append(f)
                continue

            # 4. Strict check: confirmed_failure requires deterministic method
            if f.assessment_state == "confirmed_failure" and f.test_method not in (
                "deterministic_observation",
                "automated",
                "semi_automated",
            ):
                f.assessment_state = "potential_issue"

            validated.append(f)

        return validated, rejected

    def validate_finding(
        self,
        finding: AccessibilityFinding,
        known_evidence_ids: set[str],
    ) -> bool:
        """Validate a single finding against registered evidence IDs and rules."""
        validated, _ = self.validate_findings([finding], known_evidence_ids)
        return len(validated) > 0
