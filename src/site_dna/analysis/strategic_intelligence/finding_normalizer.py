"""Finding Normalizer for Site DNA Phase 11."""

import hashlib
from typing import Any

from site_dna.schemas.strategic_intelligence import (
    ConfidenceCategory,
    NormalizedImpact,
    UnifiedFinding,
    VerificationState,
)


class FindingNormalizer:
    """Normalizes heterogeneous source agent findings into a unified model."""

    @staticmethod
    def generate_unified_id(source_phase: str, source_finding_id: str, page_url: str) -> str:
        """Derive a stable, deterministic unified finding ID."""
        raw_key = f"{source_phase}::{source_finding_id}::{page_url.strip()}"
        digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:12]
        return f"uf-{digest}"

    def normalize(
        self,
        source_phase: str,
        source_agent: str,
        source_run_id: str,
        primary_site_id: str,
        raw_finding: dict[str, Any],
    ) -> UnifiedFinding:
        """Map a single raw finding dict into the UnifiedFinding schema."""
        source_finding_id = str(raw_finding.get("finding_id", "f-unknown"))
        page_url = str(raw_finding.get("page_url") or raw_finding.get("source_page") or "")
        title = str(raw_finding.get("title", "Untitled finding"))
        title_ar = raw_finding.get("title_ar")
        description = str(raw_finding.get("description", ""))
        description_ar = raw_finding.get("description_ar")

        category = str(raw_finding.get("category", source_phase))
        subcategory = raw_finding.get("finding_type") or raw_finding.get("observation_type")

        original_sev = str(raw_finding.get("severity", "medium")).lower()

        # Map normalized impact based on original severity and domain
        impact: NormalizedImpact = "moderate_impairment"
        if original_sev in ("critical", "p0", "fatal"):
            impact = "critical_blocker"
        elif original_sev in ("high", "serious", "p1"):
            impact = "high_friction"
        elif original_sev in ("medium", "moderate", "p2"):
            impact = "moderate_impairment"
        elif original_sev in ("low", "minor", "p3", "info"):
            impact = "minor_observation"

        # Verification state
        raw_state = raw_finding.get("verification_state") or raw_finding.get("assessment_state")
        v_state: VerificationState = "confirmed_by_evidence"
        if raw_finding.get("manual_review_required"):
            v_state = "manual_review_required"
        elif raw_state in ("manual_review_required", "needs_manual_review"):
            v_state = "manual_review_required"
        elif raw_state in ("potential_issue", "potential_violation"):
            v_state = "potential_issue"
        elif raw_state in ("not_applicable", "not_assessed"):
            v_state = "not_applicable"

        # Confidence category
        conf_raw = str(raw_finding.get("confidence") or raw_finding.get("confidence_category") or "high").lower()
        conf_cat: ConfidenceCategory = "high"
        if "low" in conf_raw:
            conf_cat = "low"
        elif "med" in conf_raw:
            conf_cat = "medium"
        elif "unverif" in conf_raw:
            conf_cat = "unverified"

        # Evidence references
        evidence_ids = raw_finding.get("evidence_ids") or raw_finding.get("source_evidence_ids") or []
        if not isinstance(evidence_ids, list):
            evidence_ids = [str(evidence_ids)] if evidence_ids else []

        unified_id = self.generate_unified_id(source_phase, source_finding_id, page_url)

        return UnifiedFinding(
            unified_finding_id=unified_id,
            source_phase=source_phase,
            source_agent=source_agent,
            source_finding_id=source_finding_id,
            source_run_id=source_run_id,
            primary_site_id=primary_site_id,
            page_url=page_url,
            category=category,
            subcategory=subcategory,
            title=title,
            title_ar=title_ar,
            description=description,
            description_ar=description_ar,
            observation_type=str(raw_finding.get("observation_type", "deterministic")),
            verification_state=v_state,
            original_severity=original_sev,
            normalized_impact_category=impact,
            confidence_category=conf_cat,
            evidence_ids=[str(e) for e in evidence_ids],
            source_timestamp=raw_finding.get("created_at") or raw_finding.get("timestamp"),
            related_finding_ids=[],
            limitations=raw_finding.get("limitations"),
            limitations_ar=raw_finding.get("limitations_ar"),
        )
