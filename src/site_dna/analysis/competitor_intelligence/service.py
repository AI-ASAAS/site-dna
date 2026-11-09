"""Master Competitor Intelligence Service for Site DNA Phase 08."""

import json
import time
from pathlib import Path
from typing import Any, Optional

from site_dna.analysis.competitor_intelligence.collection_coordinator import CompetitorCollectionCoordinator
from site_dna.analysis.competitor_intelligence.company_profiles import CompetitorProfileExtractor
from site_dna.analysis.competitor_intelligence.context_builder import CompetitorContextBuilder
from site_dna.analysis.competitor_intelligence.evidence_validator import CompetitorEvidenceValidator
from site_dna.analysis.competitor_intelligence.feature_comparison import FeatureMatrixBuilder
from site_dna.analysis.competitor_intelligence.gap_analyzer import CompetitiveGapAnalyzer
from site_dna.analysis.competitor_intelligence.messaging_comparison import MessagingComparator
from site_dna.analysis.competitor_intelligence.offering_analyzer import OfferingAnalyzer
from site_dna.analysis.competitor_intelligence.opportunities import OpportunityEngine
from site_dna.analysis.competitor_intelligence.positioning_analyzer import PositioningAnalyzer
from site_dna.analysis.competitor_intelligence.pricing_comparison import PricingComparator
from site_dna.analysis.competitor_intelligence.recommendations import CompetitorRecommendationEngine
from site_dna.analysis.competitor_intelligence.relevance import CompetitorRelevanceClassifier
from site_dna.analysis.competitor_intelligence.report_builder import CompetitorReportBuilder
from site_dna.analysis.competitor_intelligence.scoring import CompetitorScoringEngine
from site_dna.analysis.competitor_intelligence.technical_benchmark import TechnicalBenchmarkAnalyzer
from site_dna.analysis.competitor_intelligence.trust_comparison import TrustComparator
from site_dna.analysis.competitor_intelligence.ux_benchmark import UXBenchmarkAnalyzer
from site_dna.analysis.competitor_intelligence.visual_benchmark import VisualBenchmarkAnalyzer
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.competitor_intelligence import (
    CompetitiveFinding,
    CompetitorAnalysisContext,
    CompetitorAnalysisRequest,
    CompetitorIntelligenceReport,
)

logger = get_logger("analysis.competitor_intelligence.service")


class CompetitorIntelligenceService:
    """End-to-end orchestration service for multi-site competitive benchmarking."""

    def __init__(self, base_dir: Path | str = "runs", settings: Optional[Settings] = None):
        self._base_dir = Path(base_dir).resolve()
        self.settings = settings or get_settings()

        self.context_builder = CompetitorContextBuilder(base_dir=self._base_dir, settings=self.settings)
        self.collection_coordinator = CompetitorCollectionCoordinator(base_dir=self._base_dir)
        self._init_components()

    def _init_components(self) -> None:
        self.relevance_classifier = CompetitorRelevanceClassifier()
        self.profile_extractor = CompetitorProfileExtractor()
        self.offering_analyzer = OfferingAnalyzer()
        self.feature_builder = FeatureMatrixBuilder()
        self.pricing_comparator = PricingComparator()
        self.positioning_analyzer = PositioningAnalyzer()
        self.messaging_comparator = MessagingComparator()
        self.visual_analyzer = VisualBenchmarkAnalyzer()
        self.ux_analyzer = UXBenchmarkAnalyzer()
        self.technical_analyzer = TechnicalBenchmarkAnalyzer()
        self.trust_comparator = TrustComparator()
        self.gap_analyzer = CompetitiveGapAnalyzer()
        self.opportunity_engine = OpportunityEngine()
        self.evidence_validator = CompetitorEvidenceValidator()
        self.scoring_engine = CompetitorScoringEngine()
        self.recommendation_engine = CompetitorRecommendationEngine()
        self.report_builder = CompetitorReportBuilder()

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    @base_dir.setter
    def base_dir(self, value: Path | str) -> None:
        self._base_dir = Path(value).resolve()
        if hasattr(self, "context_builder"):
            self.context_builder.base_dir = self._base_dir
        if hasattr(self, "collection_coordinator"):
            self.collection_coordinator.base_dir = self._base_dir
        self._init_components()

    async def analyze_competitors(self, request: CompetitorAnalysisRequest) -> CompetitorIntelligenceReport:
        """Execute full multi-site benchmark pipeline."""
        start_time = time.perf_counter()
        logger.info(
            "Initiating Competitor Intelligence benchmark for primary: %s",
            request.primary_url or request.primary_run_id,
        )

        # 1. Build Context
        context = self.context_builder.build_context(request)

        # 2. Collect / Load Evidence for all participating sites
        crawl_dataset: dict[str, dict[str, Any]] = {}
        all_sites = [context.primary_site] + context.competitor_sites

        for site in all_sites:
            cdata = await self.collection_coordinator.ensure_site_evidence(
                site,
                max_pages=request.max_pages_per_site,
                offline_mode=request.offline_mode,
            )
            crawl_dataset[site.site_id] = cdata

        # 3. Classify Relevance for each competitor
        p_crawl = crawl_dataset.get(context.primary_site.site_id, {})
        relevance_list = []
        for comp in context.competitor_sites:
            c_crawl = crawl_dataset.get(comp.site_id, {})
            rel = self.relevance_classifier.classify_relevance(
                context.primary_site,
                comp,
                p_crawl,
                c_crawl,
            )
            relevance_list.append(rel)

        # 4. Extract Profiles & Offerings
        profiles = []
        all_offerings = []
        for site in all_sites:
            cdata = crawl_dataset.get(site.site_id, {})
            prof = self.profile_extractor.extract_profile(site, cdata)
            profiles.append(prof)

            offs = self.offering_analyzer.extract_offerings(site, cdata)
            all_offerings.extend(offs)

        # 5. Build Feature Matrix
        feature_matrix = self.feature_builder.build_matrix(
            context.primary_site,
            context.competitor_sites,
            crawl_dataset,
        )

        # 6. Pricing Comparison
        pricing_records = self.pricing_comparator.compare_pricing(
            context.primary_site,
            context.competitor_sites,
            crawl_dataset,
        )

        # 7. Positioning & Messaging
        pos_assessments = [
            self.positioning_analyzer.analyze_positioning(site, crawl_dataset.get(site.site_id, {}))
            for site in all_sites
        ]
        messaging_benchmarks = self.messaging_comparator.compare_messaging(
            context.primary_site,
            context.competitor_sites,
            crawl_dataset,
        )

        # 8. Visual, UX, Technical & Trust Benchmarks
        visual_benchmarks = self.visual_analyzer.compare_visuals(context.primary_site, context.competitor_sites, {})
        ux_benchmarks = self.ux_analyzer.compare_ux(context.primary_site, context.competitor_sites, {})
        technical_benchmarks = self.technical_analyzer.compare_technical(
            context.primary_site, context.competitor_sites, {}
        )
        trust_assessments = self.trust_comparator.compare_trust(
            context.primary_site, context.competitor_sites, crawl_dataset
        )

        # 9. Gaps & Strategic Opportunities
        gaps = self.gap_analyzer.identify_gaps(
            context.primary_site,
            context.competitor_sites,
            feature_matrix,
            pricing_records,
            trust_assessments,
        )
        opportunities = self.opportunity_engine.derive_opportunities(context.primary_site, gaps, pos_assessments)

        # 10. Generate Standardized Findings
        findings: list[CompetitiveFinding] = []
        for g in gaps:
            findings.append(
                CompetitiveFinding(
                    finding_id=f"fnd-{g.gap_id}",
                    title=g.title,
                    category=g.gap_type,
                    description=g.description,
                    description_ar=g.description_ar,
                    primary_site_id=context.primary_site.site_id,
                    competitor_site_ids=g.affected_competitors,
                    source_evidence_ids=g.supporting_evidence_ids,
                    observation_type="observed" if g.supporting_evidence_ids else "derived",
                    severity="high" if "parity" in g.description.lower() else "medium",
                    confidence_category="measured",
                    potential_impact=g.strategic_implication,
                    recommended_action=g.validation_required,
                )
            )

        # Validate findings
        known_evidence_ids = {eid for f in feature_matrix if f.primary_evidence_id for eid in [f.primary_evidence_id]}
        valid_site_ids = {s.site_id for s in all_sites}
        validated_findings, _ = self.evidence_validator.validate_findings(findings, known_evidence_ids, valid_site_ids)

        # 11. Scoring
        scores = self.scoring_engine.compute_scores(
            context.primary_site,
            context.competitor_sites,
            relevance_list,
            feature_matrix,
            gaps,
            existing_scores={},
        )

        # 12. Recommendations
        recommendations = self.recommendation_engine.generate_recommendations(context.primary_site, opportunities)

        # 13. Build Complete Report
        report = self.report_builder.build_report(
            context=context,
            relevance=relevance_list,
            profiles=profiles,
            feature_matrix=feature_matrix,
            pricing=pricing_records,
            messaging=messaging_benchmarks,
            visuals=visual_benchmarks,
            ux=ux_benchmarks,
            technical=technical_benchmarks,
            trust=trust_assessments,
            gaps=gaps,
            opportunities=opportunities,
            findings=validated_findings,
            recommendations=recommendations,
            scores=scores,
        )

        duration_ms = round((time.perf_counter() - start_time) * 1000, 1)
        report.statistics.execution_duration_ms = duration_ms
        report.statistics.total_competitors_analyzed = len(context.competitor_sites)
        report.statistics.total_pages_analyzed = sum(s.pages_collected for s in all_sites)
        report.statistics.total_features_compared = len(feature_matrix)
        report.statistics.total_gaps_identified = len(gaps)
        report.statistics.total_opportunities = len(opportunities)
        report.statistics.total_recommendations = len(recommendations)

        # 14. Persist Artifacts if requested
        if request.save_results:
            self._save_artifacts(context, report)

        logger.info(
            "Completed Competitor Intelligence benchmark '%s' in %.1fms", context.comparison_run_id, duration_ms
        )
        return report

    def _save_artifacts(self, context: CompetitorAnalysisContext, report: CompetitorIntelligenceReport) -> Path:
        """Persist structured report JSON and Markdown files to disk."""
        target_dir = (
            self.base_dir
            / (context.primary_site.crawl_run_id or context.comparison_run_id)
            / "analysis"
            / "competitors"
            / context.comparison_run_id
        )
        target_dir.mkdir(parents=True, exist_ok=True)

        (target_dir / "analysis.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
        (target_dir / "report.md").write_text(report.report_markdown, encoding="utf-8")
        (target_dir / "matrix.json").write_text(
            json.dumps([f.model_dump() for f in report.feature_matrix], indent=2), encoding="utf-8"
        )
        (target_dir / "findings.json").write_text(
            json.dumps([f.model_dump() for f in report.findings], indent=2), encoding="utf-8"
        )
        (target_dir / "feature-matrix.json").write_text(
            json.dumps([f.model_dump() for f in report.feature_matrix], indent=2), encoding="utf-8"
        )
        (target_dir / "pricing-comparison.json").write_text(
            json.dumps([p.model_dump() for p in report.pricing_comparison], indent=2), encoding="utf-8"
        )
        (target_dir / "competitive-gaps.json").write_text(
            json.dumps([g.model_dump() for g in report.gaps], indent=2), encoding="utf-8"
        )
        (target_dir / "opportunities.json").write_text(
            json.dumps([o.model_dump() for o in report.opportunities], indent=2), encoding="utf-8"
        )
        (target_dir / "recommendations.json").write_text(
            json.dumps([r.model_dump() for r in report.recommendations], indent=2), encoding="utf-8"
        )

        return target_dir

    def analyze(self, request: CompetitorAnalysisRequest) -> CompetitorIntelligenceReport:
        """Synchronous execution entrypoint."""
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, self.analyze_competitors(request)).result()
        else:
            return asyncio.run(self.analyze_competitors(request))
