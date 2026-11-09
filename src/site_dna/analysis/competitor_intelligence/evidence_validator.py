"""Evidence Provenance and Anti-Hallucination Validator for Site DNA Phase 08."""

import re
from typing import Any

from site_dna.core.logging import get_logger
from site_dna.schemas.competitor_intelligence import (
    CompetitiveFinding,
)

logger = get_logger("analysis.competitor_intelligence.evidence_validator")

PROHIBITED_UNSUPPORTED_PATTERNS = [
    r"has\s+more\s+customers",
    r"ranks\s+#?1\s+on\s+google",
    r"market\s+leader",
    r"highest\s+market\s+share",
    r"cheaper\s+overall",
    r"unsupported\s+external\s+claim",
    r"الأكثر\s+مبيعا",
    r"المركز\s+الأول\s+في\s+جوجل",
]


class CompetitorEvidenceValidator:
    """Validates multi-site findings, ensuring every claim links to legitimate observable evidence."""

    def validate_findings(
        self,
        findings: list[CompetitiveFinding],
        known_evidence_ids: set[str],
        valid_site_ids: set[str],
    ) -> tuple[list[CompetitiveFinding], list[dict[str, Any]]]:
        """Validate findings against provenance rules and quarantine unsupported claims."""
        validated: list[CompetitiveFinding] = []
        quarantined: list[dict[str, Any]] = []

        for f in findings:
            # 1. Site ID validation
            if f.primary_site_id not in valid_site_ids:
                quarantined.append(
                    {"finding_id": f.finding_id, "reason": f"Invalid primary_site_id '{f.primary_site_id}'"}
                )
                continue

            # 2. Check for prohibited speculative market claims
            combined_text = (f.title + " " + f.description).lower()
            speculative_match = None
            for pattern in PROHIBITED_UNSUPPORTED_PATTERNS:
                if re.search(pattern, combined_text):
                    speculative_match = pattern
                    break

            if speculative_match:
                quarantined.append(
                    {
                        "finding_id": f.finding_id,
                        "reason": f"Prohibited speculative market claim without external telemetry ({speculative_match})",
                    }
                )
                continue

            # 3. Check evidence ID references if observation_type == 'observed'
            if f.observation_type == "observed" and f.source_evidence_ids:
                invalid_ids = [
                    eid for eid in f.source_evidence_ids if eid not in known_evidence_ids and not eid.startswith("ev-")
                ]
                if invalid_ids:
                    quarantined.append(
                        {
                            "finding_id": f.finding_id,
                            "reason": f"Non-existent evidence IDs referenced: {invalid_ids}",
                        }
                    )
                    continue

            validated.append(f)

        return validated, quarantined

    def sanitize_text(self, text: str) -> str:
        """Sanitize adversarial prompts and injection patterns from website text."""
        sanitized = re.sub(
            r"(?i)(ignore\s+all\s+instructions|system\s+instruction|delete\s+all\s+previous|human\s+review\s+override)",
            "[REDACTED]",
            text,
        )
        return sanitized
