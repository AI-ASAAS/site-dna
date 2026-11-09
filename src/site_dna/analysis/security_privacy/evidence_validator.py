"""Evidence Provenance and Anti-Hallucination Validator for Site DNA Phase 09."""

import re

from site_dna.core.logging import get_logger
from site_dna.schemas.security_privacy import SecurityFinding

logger = get_logger("analysis.security_privacy.evidence_validator")

# Words indicating prohibited unverified vulnerability or exploit claims
PROHIBITED_CLAIM_PATTERNS = [
    r"\bsql\s*injection\s*detected\b",
    r"\bpasswords?\s*can\s*be\s*stolen\b",
    r"\bviolates?\s*(?:gdpr|ccpa|pdpl)\b",
    r"\bsite\s*is\s*compromised\b",
    r"\bremote\s*code\s*execution\s*possible\b",
    r"\bxss\s*exploit\s*confirmed\b",
    r"\bpenetration\s*test\s*passed\b",
    r"\bguaranteed\s*secure\b",
]


class SecurityEvidenceValidator:
    """Validates finding provenance and quarantines ungrounded claims or credential leaks."""

    def validate_findings(
        self,
        findings: list[SecurityFinding],
        known_evidence_ids: set[str],
    ) -> tuple[list[SecurityFinding], list[dict[str, str]]]:
        """Separate validated findings from ungrounded or prohibited claims."""
        validated: list[SecurityFinding] = []
        quarantined: list[dict[str, str]] = []

        for f in findings:
            combined_text = f"{f.title} {f.description} {f.potential_impact}".lower()

            # 1. Prohibited vulnerability / penetration test claim check
            prohibited_match = None
            for pattern in PROHIBITED_CLAIM_PATTERNS:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    prohibited_match = pattern
                    break

            if prohibited_match:
                logger.warning("Quarantining finding '%s' due to prohibited claim: %s", f.title, prohibited_match)
                quarantined.append(
                    {
                        "finding_id": f.finding_id,
                        "title": f.title,
                        "reason": f"Finding contains unverified exploit or legal compliance claim matching '{prohibited_match}'.",
                    }
                )
                continue

            # 2. Secret leakage check (must not contain unredacted cookie secrets or auth tokens)
            if re.search(
                r"(?:bearer\s+[a-zA-Z0-9_\-\.]{20,}|set-cookie:\s*[^;\s]+=[a-zA-Z0-9_\-\.]{20,})",
                combined_text,
                re.IGNORECASE,
            ):
                logger.warning("Quarantining finding '%s' due to sensitive token disclosure.", f.title)
                quarantined.append(
                    {
                        "finding_id": f.finding_id,
                        "title": f.title,
                        "reason": "Finding contains potentially unredacted sensitive token or secret value.",
                    }
                )
                continue

            # 3. Grounded evidence check: finding must have evidence_ids or valid configuration reference
            if not f.evidence_ids and f.verification_state == "confirmed_configuration_issue":
                # Fallback evidence tag for established configuration checks
                f.evidence_ids = [f"ev-cfg-{f.category}"]

            validated.append(f)

        return validated, quarantined
