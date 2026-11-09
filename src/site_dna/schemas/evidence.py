"""Evidence schema for traceable Site DNA data extractions."""

from datetime import datetime, timezone
from typing import Any, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

EvidenceType = Literal["observed", "derived", "heuristic"]


class EvidenceRecord(BaseModel):
    """An atomic, auditable piece of evidence gathered during discovery/crawling.

    Attributes:
        id: Unique identifier for this evidence record.
        run_id: The ID of the discovery run that produced this evidence.
        source_url: The original URL where the evidence was extracted.
        final_url: The final canonical URL (after any redirects).
        evidence_type: Classification of evidence ('observed' directly from HTML/headers,
            'derived' from parsing/transforms, or 'heuristic' from classification).
        field_reference: Normalized target field (e.g. 'page.title', 'page.headings.h1').
        exact_value: The exact extracted value or serialized representation.
        timestamp: Time of extraction in UTC.
        extraction_method: Method/parser used to collect the evidence (e.g. 'bs4_css', 'http_headers').
        metadata: Additional contextual info (e.g. line numbers, tag attributes, confidence).
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    source_url: str
    final_url: Optional[str] = None
    evidence_type: EvidenceType = "observed"
    field_reference: str
    exact_value: Any
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    extraction_method: str = "extractor"
    metadata: dict[str, Any] = Field(default_factory=dict)
