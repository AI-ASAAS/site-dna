"""Evidence validator enforcing auditable grounding and quarantining unverified claims."""

from pydantic import BaseModel, Field

from site_dna.core.logging import get_logger
from site_dna.schemas.ux_ui import UXFinding
from site_dna.schemas.visual import VisualEvidenceRecord

logger = get_logger("analysis.ux_ui.evidence_validator")


class UXValidationSummary(BaseModel):
    """Structured audit validation summary separating grounded findings from rejected claims."""

    total_findings: int = 0
    validated_findings: list[UXFinding] = Field(default_factory=list)
    rejected_findings: list[UXFinding] = Field(default_factory=list)
    quarantine_reasons: dict[str, str] = Field(default_factory=dict)


class UXEvidenceValidator:
    """Validates that findings reference actual collected Phase 02/03 records and pages."""

    def __init__(
        self,
        evidence_index: dict[str, VisualEvidenceRecord],
        valid_page_urls: set[str],
    ):
        self.evidence_index = evidence_index
        self.valid_page_urls = valid_page_urls

    def validate_findings(self, findings: list[UXFinding]) -> UXValidationSummary:
        """Validate findings against ground-truth evidence and quarantine invalid assertions."""
        summary = UXValidationSummary(total_findings=len(findings))

        for f in findings:
            is_valid = True
            rejection_reason = None

            # Rule 1: Page URL must belong to the analyzed crawl set
            if f.source_page and f.source_page not in self.valid_page_urls:
                is_valid = False
                rejection_reason = f"الملاحظة تدعي فحص صفحة غير موجودة في العينة المستكشفة: {f.source_page}"

            # Rule 2: Viewport must be valid
            if f.viewport not in ("desktop", "mobile", "tablet", "all"):
                is_valid = False
                rejection_reason = f"نافذة العرض غير صالحة: {f.viewport}"

            # Rule 3: For findings claiming specific evidence IDs, all referenced IDs must exist
            if f.evidence_ids:
                missing_ids = [eid for eid in f.evidence_ids if eid not in self.evidence_index]
                if missing_ids:
                    is_valid = False
                    rejection_reason = f"الملاحظة تشير إلى معرفات أدلة غير مسجلة في فهرس المرحلة 03: {missing_ids}"

            # Rule 4: Reject claims alleging broken interactions without test execution proof
            lower_desc = f.description.lower()
            lower_title = f.title.lower()
            if (
                "broken" in lower_desc
                or "fails to submit" in lower_desc
                or "معطل" in lower_title
                or "فشل الإرسال" in lower_title
            ):
                if f.observation_type not in ("observed", "derived"):
                    is_valid = False
                    rejection_reason = "لا يمكن ادعاء تعطل زر أو فشل إرسال نموذج برمجياً استناداً إلى الرأي البصري فقط دون اختبار تفاعلي مباشر."

            if is_valid:
                f.is_validated = True
                f.rejection_reason = None
                summary.validated_findings.append(f)
            else:
                f.is_validated = False
                f.rejection_reason = rejection_reason
                summary.rejected_findings.append(f)
                summary.quarantine_reasons[f.finding_id] = rejection_reason or "Unknown validation error"
                logger.warning("Quarantined unsupported UX finding %s: %s", f.finding_id, rejection_reason)

        return summary
