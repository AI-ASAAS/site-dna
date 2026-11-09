"""CrewAI Strategic Intelligence Tool for Site DNA Phase 11."""

import json
from typing import Any, Optional, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from site_dna.analysis.strategic_intelligence.context_builder import StrategicContextBuilder
from site_dna.analysis.strategic_intelligence.deduplication import FindingDeduplicator
from site_dna.analysis.strategic_intelligence.finding_normalizer import FindingNormalizer
from site_dna.schemas.strategic_intelligence import StrategicAnalysisRequest


class StrategicIntelligenceToolInput(BaseModel):
    """Input schema for StrategicIntelligenceTool."""

    crawl_run_id: str = Field(..., description="Target crawl run ID to synthesize")
    language: str = Field(default="ar", description="Language of analysis ('ar' or 'en')")


class StrategicIntelligenceTool(BaseTool):
    """Tool enabling CrewAI agents to inspect cross-agent findings and detect duplicates."""

    name: str = "strategic_intelligence_tool"
    description: str = (
        "Ingests multi-agent analysis artifacts (Phases 04-10) for a given crawl run, "
        "normalizes findings, and returns structured duplicate groups and coverage metrics."
    )
    args_schema: Type[BaseModel] = StrategicIntelligenceToolInput

    def _run(self, crawl_run_id: str, language: str = "ar") -> str:
        """Execute deterministic cross-agent evidence ingestion."""
        try:
            builder = StrategicContextBuilder()
            ctx = builder.build_context(StrategicAnalysisRequest(crawl_run_id=crawl_run_id, language=language))

            normalizer = FindingNormalizer()
            raw_findings = []
            for phase_key, art in ctx["loaded_artifacts"].items():
                data = art["data"]
                meta = art["meta"]
                run_id = art["run_id"]
                for rf in data.get("findings", []):
                    uf = normalizer.normalize(
                        source_phase=phase_key,
                        source_agent=meta.display_name,
                        source_run_id=run_id,
                        primary_site_id=ctx["canonical_origin"],
                        raw_finding=rf,
                    )
                    raw_findings.append(uf)

            deduplicator = FindingDeduplicator()
            findings, dup_groups = deduplicator.deduplicate(raw_findings)

            summary = {
                "status": "success",
                "crawl_run_id": crawl_run_id,
                "coverage_percentage": ctx["coverage"].coverage_percentage,
                "available_agents": ctx["coverage"].available_agents,
                "raw_findings_count": len(raw_findings),
                "duplicate_groups_count": len(dup_groups),
                "duplicate_groups": [
                    {
                        "title": g.canonical_title,
                        "agents": g.source_agents,
                        "reason": g.deduplication_reason,
                    }
                    for g in dup_groups
                ],
            }
            return json.dumps(summary, indent=2, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
