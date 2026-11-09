"""Evidence generation and tracking for Site DNA auditable intelligence."""

from typing import Any, Optional
from uuid import uuid4

from site_dna.schemas.evidence import EvidenceRecord, EvidenceType


class EvidenceCollector:
    """Collects and organizes granular, traceable evidence records during a crawl run."""

    def __init__(self, run_id: Optional[str] = None):
        self.run_id = run_id or str(uuid4())
        self.records: list[EvidenceRecord] = []

    def add(
        self,
        source_url: str,
        field_reference: str,
        exact_value: Any,
        evidence_type: EvidenceType = "observed",
        extraction_method: str = "extractor",
        final_url: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> EvidenceRecord:
        """Record an atomic piece of evidence."""
        record = EvidenceRecord(
            run_id=self.run_id,
            source_url=source_url,
            final_url=final_url or source_url,
            evidence_type=evidence_type,
            field_reference=field_reference,
            exact_value=exact_value,
            extraction_method=extraction_method,
            metadata=metadata or {},
        )
        self.records.append(record)
        return record

    def get_all(self) -> list[EvidenceRecord]:
        return list(self.records)

    def count(self) -> int:
        return len(self.records)
