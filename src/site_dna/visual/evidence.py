"""Visual evidence recording and traceability engine."""

from typing import Any, Optional
from uuid import uuid4

from site_dna.schemas.visual import ConfidenceLevel, EvidenceCategory, VisualEvidenceRecord


class VisualEvidenceCollector:
    """Collects and organizes granular visual evidence records for auditability."""

    def __init__(self, crawl_run_id: str, visual_run_id: Optional[str] = None):
        self.crawl_run_id = crawl_run_id
        self.visual_run_id = visual_run_id or str(uuid4())
        self.records: list[VisualEvidenceRecord] = []

    def add(
        self,
        page_url: str,
        viewport_profile: str,
        evidence_category: EvidenceCategory,
        field_reference: str,
        observed_value: Any,
        collection_method: str = "playwright",
        confidence_category: ConfidenceLevel = "observed",
        screenshot_reference: Optional[str] = None,
    ) -> VisualEvidenceRecord:
        """Create and store an atomic piece of visual evidence."""
        record = VisualEvidenceRecord(
            crawl_run_id=self.crawl_run_id,
            visual_run_id=self.visual_run_id,
            page_url=page_url,
            viewport_profile=viewport_profile,
            evidence_category=evidence_category,
            confidence_category=confidence_category,
            field_reference=field_reference,
            observed_value=observed_value,
            collection_method=collection_method,
            screenshot_reference=screenshot_reference,
        )
        self.records.append(record)
        return record

    def get_all(self) -> list[VisualEvidenceRecord]:
        return list(self.records)

    def get_for_page(self, page_url: str) -> list[VisualEvidenceRecord]:
        return [r for r in self.records if r.page_url == page_url]

    def count(self) -> int:
        return len(self.records)
