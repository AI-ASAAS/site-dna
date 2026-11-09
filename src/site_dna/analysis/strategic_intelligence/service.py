"""Strategic Intelligence & Unified Action Roadmap Service for Site DNA Phase 11."""

import json
from pathlib import Path
from typing import Any, Optional
import uuid

from site_dna.analysis.strategic_intelligence.action_backlog import ActionBacklogGenerator
from site_dna.analysis.strategic_intelligence.conflict_detection import ConflictDetector
from site_dna.analysis.strategic_intelligence.context_builder import StrategicContextBuilder, validate_run_id
from site_dna.analysis.strategic_intelligence.deduplication import FindingDeduplicator
from site_dna.analysis.strategic_intelligence.dependency_planner import DependencyPlanner
from site_dna.analysis.strategic_intelligence.evidence_validator import StrategicEvidenceValidator
from site_dna.analysis.strategic_intelligence.finding_normalizer import FindingNormalizer
from site_dna.analysis.strategic_intelligence.human_review import HumanReviewGenerator
from site_dna.analysis.strategic_intelligence.measurement_plan import MeasurementPlanner
from site_dna.analysis.strategic_intelligence.opportunity_synthesis import OpportunitySynthesizer
from site_dna.analysis.strategic_intelligence.relationship_graph import RelationshipGraphEngine
from site_dna.analysis.strategic_intelligence.report_builder import StrategicReportBuilder
from site_dna.analysis.strategic_intelligence.roadmap_builder import RoadmapBuilder
from site_dna.analysis.strategic_intelligence.root_cause_candidates import RootCauseAnalyzer
from site_dna.analysis.strategic_intelligence.scoring import StrategicScoringEngine
from site_dna.analysis.strategic_intelligence.verification_planner import VerificationPlanner
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.strategic_intelligence import (
    RoadmapAction,
    StrategicAnalysisRequest,
    StrategicIntelligenceReport,
)

logger = get_logger("analysis.strategic_intelligence.service")


class StrategicIntelligenceService:
    """End-to-end service coordinating multi-agent normalization, synthesis, and roadmap generation."""

    def __init__(self, settings: Optional[Settings] = None, base_runs_dir: Optional[str] = None):
        self.settings = settings or get_settings()
        self.base_runs_dir = Path(base_runs_dir or "runs").resolve()
        self.context_builder = StrategicContextBuilder(base_runs_dir=str(self.base_runs_dir), settings=self.settings)
        self.normalizer = FindingNormalizer()
        self.deduplicator = FindingDeduplicator()
        self.conflict_detector = ConflictDetector()
        self.root_cause_analyzer = RootCauseAnalyzer()
        self.opportunity_synthesizer = OpportunitySynthesizer()
        self.backlog_generator = ActionBacklogGenerator()
        self.dependency_planner = DependencyPlanner()
        self.roadmap_builder = RoadmapBuilder()
        self.verification_planner = VerificationPlanner()
        self.measurement_planner = MeasurementPlanner()
        self.human_review_generator = HumanReviewGenerator()
        self.evidence_validator = StrategicEvidenceValidator()
        self.scoring_engine = StrategicScoringEngine()
        self.report_builder = StrategicReportBuilder()

    async def analyze_strategy(self, request: StrategicAnalysisRequest) -> StrategicIntelligenceReport:
        """Execute deterministic cross-agent synthesis and generate prioritized roadmap."""
        ctx = self.context_builder.build_context(request)

        # 1. Normalize all available findings
        raw_findings = []
        for phase_key, art in ctx["loaded_artifacts"].items():
            data = art["data"]
            meta = art["meta"]
            run_id = art["run_id"]
            for rf in data.get("findings", []):
                uf = self.normalizer.normalize(
                    source_phase=phase_key,
                    source_agent=meta.display_name,
                    source_run_id=run_id,
                    primary_site_id=ctx["canonical_origin"],
                    raw_finding=rf,
                )
                raw_findings.append(uf)

        # 2. Deduplicate findings
        unified_findings, duplicate_groups = self.deduplicator.deduplicate(raw_findings)

        # 3. Model semantic relationships
        graph_engine = RelationshipGraphEngine()
        relationships = graph_engine.build_relationships_from_findings_and_groups(unified_findings, duplicate_groups)

        # 4. Detect conflicts
        conflicts = self.conflict_detector.detect_conflicts(unified_findings)
        valid_finding_ids = {f.unified_finding_id for f in unified_findings}
        conflicts = self.evidence_validator.validate_conflicts(conflicts, valid_finding_ids)

        # 5. Root cause hypotheses
        root_causes = self.root_cause_analyzer.analyze_root_causes(unified_findings)

        # 6. Strategic opportunities
        opportunities = self.opportunity_synthesizer.synthesize_opportunities(unified_findings)

        # 7. Action Backlog
        raw_actions = self.backlog_generator.generate_backlog(
            unified_findings, duplicate_groups, max_actions=request.max_actions
        )

        # Validate actions
        validated_actions = [a for a in raw_actions if self.evidence_validator.validate_action(a, valid_finding_ids)]

        # 8. Dependency sequence and waves
        sequenced_actions = self.dependency_planner.resolve_dependencies_and_waves(validated_actions)
        self.evidence_validator.validate_plan_acyclicity(sequenced_actions)

        # 9. Roadmap waves
        waves = self.roadmap_builder.build_waves(sequenced_actions)

        # 10. Verification and Measurement plans
        verification_plans = self.verification_planner.build_verification_plans(sequenced_actions)
        measurement_plans = self.measurement_planner.build_measurement_plan(unified_findings)

        # 11. Human Review Tasks
        manual_reviews = self.human_review_generator.generate_review_tasks(unified_findings, conflicts, root_causes)

        # 12. Statistics
        stats = self.scoring_engine.compute_statistics(
            coverage=ctx["coverage"],
            raw_findings_count=len(raw_findings),
            unified_findings=unified_findings,
            duplicate_groups=duplicate_groups,
            conflicts=conflicts,
            root_causes=root_causes,
            opportunities=opportunities,
            actions=sequenced_actions,
            manual_reviews=manual_reviews,
        )

        strat_id = f"strat-{uuid.uuid4().hex[:12]}"

        report = StrategicIntelligenceReport(
            strategic_run_id=strat_id,
            crawl_run_id=request.crawl_run_id,
            target_url=ctx["target_url"],
            canonical_origin=ctx["canonical_origin"],
            model_name="gemini-3.6-flash",
            ai_status="deterministic_fallback" if request.deterministic_only else "completed",
            coverage=ctx["coverage"],
            statistics=stats,
            unified_findings=unified_findings,
            duplicate_groups=duplicate_groups,
            relationships=relationships,
            conflicts=conflicts,
            root_cause_candidates=root_causes,
            opportunities=opportunities,
            actions=sequenced_actions,
            waves=waves,
            verification_plans=verification_plans,
            measurement_plans=measurement_plans,
            manual_reviews=manual_reviews,
            report_markdown="",
            executive_summary_markdown="",
        )

        # Generate markdown reports
        report.report_markdown = self.report_builder.build_report_markdown(report)
        report.executive_summary_markdown = self.report_builder.build_executive_summary(report)

        if request.save_results:
            self._save_artifacts(report)

        return report

    def _save_artifacts(self, report: StrategicIntelligenceReport) -> Path:
        """Persist structured JSON and Markdown artifacts to disk."""
        run_dir = (
            self.base_runs_dir
            / report.crawl_run_id
            / "analysis"
            / "strategic-intelligence"
            / report.strategic_run_id
        )
        run_dir.mkdir(parents=True, exist_ok=True)

        # 1. Main analysis.json
        (run_dir / "analysis.json").write_text(
            report.model_dump_json(indent=2),
            encoding="utf-8",
        )

        # 2. Markdown reports
        (run_dir / "report.md").write_text(report.report_markdown, encoding="utf-8")
        (run_dir / "executive-summary.md").write_text(report.executive_summary_markdown, encoding="utf-8")

        # 3. Modular JSON artifacts
        (run_dir / "source-coverage.json").write_text(
            report.coverage.model_dump_json(indent=2),
            encoding="utf-8",
        )
        (run_dir / "unified-findings.json").write_text(
            json.dumps([f.model_dump() for f in report.unified_findings], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (run_dir / "duplicate-groups.json").write_text(
            json.dumps([g.model_dump() for g in report.duplicate_groups], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (run_dir / "relationships.json").write_text(
            json.dumps([r.model_dump() for r in report.relationships], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (run_dir / "conflicts.json").write_text(
            json.dumps([c.model_dump() for c in report.conflicts], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (run_dir / "root-cause-candidates.json").write_text(
            json.dumps([rc.model_dump() for rc in report.root_cause_candidates], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (run_dir / "opportunities.json").write_text(
            json.dumps([op.model_dump() for op in report.opportunities], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (run_dir / "action-backlog.json").write_text(
            json.dumps([a.model_dump() for a in report.actions], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (run_dir / "roadmap.json").write_text(
            json.dumps([w.model_dump() for w in report.waves], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (run_dir / "verification-plans.json").write_text(
            json.dumps([v.model_dump() for v in report.verification_plans], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (run_dir / "measurement-plan.json").write_text(
            json.dumps([m.model_dump() for m in report.measurement_plans], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (run_dir / "manual-review.json").write_text(
            json.dumps([hr.model_dump() for hr in report.manual_reviews], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (run_dir / "execution-summary.json").write_text(
            report.statistics.model_dump_json(indent=2),
            encoding="utf-8",
        )

        return run_dir
