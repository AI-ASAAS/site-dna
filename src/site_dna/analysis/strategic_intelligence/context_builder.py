"""Strategic Intelligence Context Builder for Site DNA Phase 11."""

import json
import re
from pathlib import Path
from typing import Any, Optional

from site_dna.analysis.strategic_intelligence.source_registry import SUPPORTED_SOURCE_AGENTS
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.core.security import SecurityValidationError
from site_dna.schemas.strategic_intelligence import (
    AgentCoverageRecord,
    SourceCoverageAssessment,
    StrategicAnalysisRequest,
)

logger = get_logger("analysis.strategic_intelligence.context_builder")

_RUN_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]+$")


def validate_run_id(run_id: str) -> None:
    """Validate run ID syntax to prevent path traversal."""
    if not run_id or not _RUN_ID_REGEX.match(run_id):
        raise SecurityValidationError(f"Invalid or unsafe run ID format: '{run_id}'")


class StrategicContextBuilder:
    """Discovers, validates, and ingests multi-agent analysis artifacts."""

    def __init__(self, base_runs_dir: Optional[str] = None, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.base_runs_dir = Path(base_runs_dir or "runs").resolve()

    def build_context(self, request: StrategicAnalysisRequest) -> dict[str, Any]:
        """Load and validate all available source phase artifacts for target crawl run."""
        validate_run_id(request.crawl_run_id)

        crawl_dir = self.base_runs_dir / request.crawl_run_id
        if not crawl_dir.exists() or not crawl_dir.is_dir():
            raise FileNotFoundError(f"Primary crawl run directory not found: '{request.crawl_run_id}'")

        # Ingest target website metadata
        crawl_file = crawl_dir / "crawl.json"
        target_url = ""
        canonical_origin = ""
        inspected_pages: list[str] = []

        if crawl_file.exists():
            try:
                cdata = json.loads(crawl_file.read_text(encoding="utf-8"))
                target_url = cdata.get("target_url", "")
                winfo = cdata.get("website_info", {})
                canonical_origin = winfo.get("canonical_origin") or target_url
                for p in cdata.get("pages", []):
                    if isinstance(p, dict) and p.get("url"):
                        inspected_pages.append(p["url"])
            except Exception as e:
                logger.warning("Failed to parse crawl.json in %s: %s", request.crawl_run_id, e)

        # Fallback to execution.json if crawl.json was missing or empty
        exec_file = crawl_dir / "execution.json"
        if (not target_url or not canonical_origin) and exec_file.exists():
            try:
                edata = json.loads(exec_file.read_text(encoding="utf-8"))
                target_url = target_url or edata.get("url", "")
                canonical_origin = canonical_origin or edata.get("canonical_origin", target_url)
            except Exception:
                pass

        if not target_url:
            target_url = f"https://{request.crawl_run_id}.local"
            canonical_origin = target_url

        # Ingest source agent artifacts
        loaded_artifacts: dict[str, Any] = {}
        agent_records: list[AgentCoverageRecord] = []
        available_agents: list[str] = []
        partial_agents: list[str] = []
        missing_agents: list[str] = []

        analysis_root = crawl_dir / "analysis"

        for phase_key, meta in SUPPORTED_SOURCE_AGENTS.items():
            # Mode B explicit override support
            custom_run_id = None
            if request.source_run_ids and phase_key in request.source_run_ids:
                custom_run_id = request.source_run_ids[phase_key]
                validate_run_id(custom_run_id)

            phase_dir = analysis_root / meta.artifact_subfolder
            target_subrun_dir = None

            if phase_dir.exists() and phase_dir.is_dir():
                subdirs = [d for d in phase_dir.iterdir() if d.is_dir()]
                if custom_run_id:
                    matched = [d for d in subdirs if d.name == custom_run_id]
                    if matched:
                        target_subrun_dir = matched[0]
                elif subdirs:
                    # Choose latest by modification time
                    target_subrun_dir = sorted(subdirs, key=lambda d: d.stat().st_mtime, reverse=True)[0]

            if target_subrun_dir:
                art_file = target_subrun_dir / meta.primary_artifact_file
                if art_file.exists():
                    try:
                        data = json.loads(art_file.read_text(encoding="utf-8"))
                        loaded_artifacts[phase_key] = {
                            "meta": meta,
                            "run_id": target_subrun_dir.name,
                            "artifact_path": str(art_file),
                            "data": data,
                        }
                        findings = data.get("findings", [])
                        f_count = len(findings) if isinstance(findings, list) else 0
                        pages_count = len(inspected_pages) if inspected_pages else 1

                        status_val = "completed" if f_count >= 0 else "partial"
                        available_agents.append(phase_key)
                        agent_records.append(
                            AgentCoverageRecord(
                                agent_id=phase_key,
                                agent_name=meta.display_name,
                                status=status_val,
                                run_id=target_subrun_dir.name,
                                findings_count=f_count,
                                pages_inspected=pages_count,
                                has_ai_interpretation=bool(data.get("model_name")),
                                limitations=None,
                            )
                        )
                        continue
                    except Exception as e:
                        logger.warning("Corrupted artifact in %s: %s", art_file, e)
                        partial_agents.append(phase_key)
                        agent_records.append(
                            AgentCoverageRecord(
                                agent_id=phase_key,
                                agent_name=meta.display_name,
                                status="partial",
                                run_id=target_subrun_dir.name,
                                findings_count=0,
                                pages_inspected=0,
                                has_ai_interpretation=False,
                                limitations=f"Corrupted or invalid JSON artifact: {e}",
                            )
                        )
                        continue

            # If not found
            missing_agents.append(phase_key)
            agent_records.append(
                AgentCoverageRecord(
                    agent_id=phase_key,
                    agent_name=meta.display_name,
                    status="unavailable",
                    run_id=None,
                    findings_count=0,
                    pages_inspected=0,
                    has_ai_interpretation=False,
                    limitations="Phase output not found in crawl run analysis directory.",
                )
            )

        total_potential = len(SUPPORTED_SOURCE_AGENTS)
        coverage_pct = round((len(available_agents) / total_potential) * 100.0, 1) if total_potential else 0.0

        coverage = SourceCoverageAssessment(
            total_potential_agents=total_potential,
            available_agents=available_agents,
            partial_agents=partial_agents,
            missing_agents=missing_agents,
            coverage_percentage=coverage_pct,
            agent_records=agent_records,
            total_pages_covered=len(inspected_pages),
            data_freshness_timestamp=None,
        )

        return {
            "crawl_run_id": request.crawl_run_id,
            "target_url": target_url,
            "canonical_origin": canonical_origin,
            "inspected_pages": inspected_pages,
            "loaded_artifacts": loaded_artifacts,
            "coverage": coverage,
        }
