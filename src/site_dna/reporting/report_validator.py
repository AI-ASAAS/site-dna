"""Zero-hallucination and evidence grounding validator for Site DNA Final Reports."""

import re
from typing import Any

from site_dna.core.logging import get_logger

logger = get_logger("reporting.validator")

# Banned speculative phrases that indicate ungrounded hallucination
_SPECULATIVE_PATTERNS = [
    re.compile(r"\b(?:revenue|sales|profit)\s*(?:increase|boost|uplift)\s*by\s*\d+%", re.IGNORECASE),
    re.compile(r"\b(?:conversion\s*rate|ROI)\b.*?\b\d+%", re.IGNORECASE),
    re.compile(r"\bguaranteed\s*(?:\$|SAR|USD|\d+)", re.IGNORECASE),
    re.compile(r"\b(?:guarantee|guaranteed)\s*\d+%\s*ROI\b", re.IGNORECASE),
    re.compile(r"\b(?:100%|completely)\s*(?:secure|hack-proof|uncrackable)", re.IGNORECASE),
    re.compile(r"\bofficially\s*certified\s*by\s*W3C\b", re.IGNORECASE),
    re.compile(r"\b(?:GDPR|HIPAA|WCAG)\s*(?:certified|compliant)\b", re.IGNORECASE),
    re.compile(r"\bguaranteed\s*(?:#1|first\s*page)\s*google\b", re.IGNORECASE),
    re.compile(r"زيادة\s*(?:الأرباح|المبيعات|الإيرادات|معدل\s*التحويل)\s*بنسبة\s*\d+%", re.IGNORECASE),
    re.compile(r"عائد\s*(?:استثماري|على\s*الاستثمار)\s*بنسبة", re.IGNORECASE),
    re.compile(r"حماية\s*(?:مطلقة|مكتملة\s*100%|عسكرية)", re.IGNORECASE),
    re.compile(r"شهادة\s*(?:اعتماد\s*رسمية\s*من\s*W3C|رسمية|معتمدة)", re.IGNORECASE),
]


class ValidationResult:
    """Result object supporting both tuple unpacking and dict-like access."""

    def __init__(self, is_valid: bool, violations: list[str], warnings: list[str]):
        self.is_valid = is_valid
        self.violations = violations
        self.warnings = warnings

    def __iter__(self):
        return iter((self.is_valid, self.violations, self.warnings))

    def __getitem__(self, item: str) -> Any:
        if item == "is_valid":
            return self.is_valid
        elif item == "violations":
            return self.violations
        elif item == "warnings":
            return self.warnings
        raise KeyError(item)

    def get(self, item: str, default: Any = None) -> Any:
        try:
            return self[item]
        except KeyError:
            return default


class ReportIntegrityValidator:
    """Validates that final report claims strictly align with verified technical evidence."""

    def __init__(self, context: Any = None):
        self.ctx = context
        self.violations: list[str] = []
        self.warnings: list[str] = []

    def validate(self, context: Any = None) -> ValidationResult:
        """Run all verification checks. Returns ValidationResult."""
        if context is not None:
            self.ctx = context
        assert self.ctx is not None, "FinalReportContext required for validation"

        self.violations.clear()
        self.warnings.clear()

        self._check_for_speculative_claims()
        self._check_evidence_grounding()
        self._check_missing_stage_disclosures()
        self._check_score_consistency()

        is_valid = len(self.violations) == 0
        return ValidationResult(is_valid, list(self.violations), list(self.warnings))

    def _check_for_speculative_claims(self) -> None:
        """Scan executive narrative and recommendation titles for fabricated financial or certification claims."""
        texts_to_scan = [
            self.ctx.executive_summary_md,
            self.ctx.executive_summary_ar,
            *self.ctx.key_conclusions,
            *[r.title for r in self.ctx.recommendations],
            *[r.description for r in self.ctx.recommendations],
        ]

        for text in texts_to_scan:
            if not text:
                continue
            for pat in _SPECULATIVE_PATTERNS:
                if pat.search(text):
                    match = pat.search(text).group(0)
                    self.violations.append(
                        f"Zero-Hallucination violation: detected ungrounded speculative claim '{match}'"
                    )

    def _check_evidence_grounding(self) -> None:
        """Ensure that findings and recommendations contain traceable evidence links."""
        for finding in self.ctx.findings:
            if finding.severity in ("critical", "high") and not finding.evidence_ids and not finding.affected_urls:
                self.warnings.append(
                    f"Finding '{finding.finding_id}' ({finding.severity}) has no explicit evidence IDs attached."
                )

    def _check_missing_stage_disclosures(self) -> None:
        """Verify that when any standard stage is missing, it is documented in limitations."""
        if self.ctx.missing_stages and not self.ctx.limitations:
            self.violations.append(
                "Missing stage disclosure violation: missing stages present but no limitations disclosed."
            )

    def _check_score_consistency(self) -> None:
        """Check that scores are within valid ranges [0, 100]."""
        for stage, sc in self.ctx.scores.items():
            if sc < 0.0 or sc > 100.0:
                self.violations.append(f"Invalid score for '{stage}': {sc} is out of bounds [0, 100].")
        if self.ctx.strategic_index is not None and (self.ctx.strategic_index < 0.0 or self.ctx.strategic_index > 100.0):
            self.violations.append(f"Invalid strategic index: {self.ctx.strategic_index} is out of bounds [0, 100].")
