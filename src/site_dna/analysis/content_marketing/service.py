"""Main orchestration service for Site DNA Content & Marketing Intelligence."""

import time
import uuid
from pathlib import Path
from typing import Optional

from site_dna.analysis.content_marketing.consistency_analyzer import ConsistencyAnalyzer
from site_dna.analysis.content_marketing.content_gaps import ContentGapAnalyzer
from site_dna.analysis.content_marketing.content_inventory import ContentInventoryBuilder
from site_dna.analysis.content_marketing.context_builder import ContentContextBuilder
from site_dna.analysis.content_marketing.copy_proposals import CopyProposalsEngine
from site_dna.analysis.content_marketing.cta_analyzer import CTAContentAnalyzer
from site_dna.analysis.content_marketing.evidence_validator import ContentEvidenceValidator
from site_dna.analysis.content_marketing.messaging_analyzer import MessagingAnalyzer
from site_dna.analysis.content_marketing.multimodal_adapter import ContentMultimodalAdapter
from site_dna.analysis.content_marketing.recommendations import ContentRecommendationEngine
from site_dna.analysis.content_marketing.report_builder import ContentReportBuilder
from site_dna.analysis.content_marketing.scoring import ContentScoringEngine
from site_dna.analysis.content_marketing.service_content import ServiceContentAnalyzer
from site_dna.analysis.content_marketing.trust_analyzer import TrustAnalyzer
from site_dna.analysis.content_marketing.value_proposition import ValuePropositionAnalyzer
from site_dna.analysis.content_marketing.voice_analyzer import VoiceAnalyzer
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.content_marketing import (
    AnalysisExecutionStatus,
    ContentAnalysisRequest,
    ContentAnalysisStatistics,
    ContentFinding,
    ContentMarketingReport,
)

logger = get_logger("analysis.content_marketing.service")


class ContentMarketingAnalysisService:
    """Orchestrates multi-layer Content & Marketing Intelligence analysis."""

    def __init__(self, settings: Optional[Settings] = None, base_dir: str = "runs"):
        self.settings = settings or get_settings()
        self.base_dir = Path(base_dir).resolve()
        self.context_builder = ContentContextBuilder(base_dir=str(self.base_dir))
        self.ai_adapter = ContentMultimodalAdapter(settings=self.settings)

    def analyze_content(
        self,
        request: ContentAnalysisRequest,
        offline_mode: Optional[bool] = None,
    ) -> ContentMarketingReport:
        """Execute complete Content & Marketing audit."""
        start_time = time.time()
        effective_offline = offline_mode if offline_mode is not None else request.offline_mode

        run_id = f"cnt-{uuid.uuid4().hex[:12]}"
        logger.info(
            "Starting content marketing analysis: run_id=%s, crawl_run_id=%s",
            run_id,
            request.crawl_run_id,
        )

        # 1. Build context
        pages, evidence_index, target_origin, website_info = self.context_builder.build_context(
            crawl_run_id=request.crawl_run_id,
            visual_run_id=request.visual_run_id,
            max_pages=request.max_pages or self.settings.content_analysis_max_pages,
        )

        # 2. Content Inventory
        inventory = ContentInventoryBuilder.build_inventory(pages)

        # 3. Layer B: Deterministic Analyzers
        raw_findings: list[ContentFinding] = []

        value_prop, vp_findings = ValuePropositionAnalyzer.analyze(pages)
        raw_findings.extend(vp_findings)

        messaging, msg_findings = MessagingAnalyzer.analyze(pages)
        raw_findings.extend(msg_findings)

        services, srv_findings = ServiceContentAnalyzer.analyze(pages)
        raw_findings.extend(srv_findings)

        ctas, cta_findings = CTAContentAnalyzer.analyze(pages)
        raw_findings.extend(cta_findings)

        claims, trust_findings = TrustAnalyzer.analyze(pages)
        raw_findings.extend(trust_findings)

        voice, voice_findings = VoiceAnalyzer.analyze(pages)
        raw_findings.extend(voice_findings)

        consistency_findings = ConsistencyAnalyzer.analyze(pages)
        raw_findings.extend(consistency_findings)

        content_gaps = ContentGapAnalyzer.analyze(pages)

        # 4. Layer C: Multimodal AI Reasoning (Gemini 3.6 Flash)
        ai_status: AnalysisExecutionStatus = "completed"
        model_calls = 0
        ai_data = None

        if not request.deterministic_only and not effective_offline:
            model_calls += 1
            ai_data, ai_status, ai_duration = self.ai_adapter.analyze_content(
                pages=pages,
                target_origin=target_origin,
                offline_mode=effective_offline,
            )
            if ai_data and "ai_findings" in ai_data:
                for af in ai_data.get("ai_findings", []):
                    try:
                        raw_findings.append(
                            ContentFinding(
                                finding_id=af.get("finding_id", f"CF-AI-{len(raw_findings) + 1}"),
                                title=af.get("title", "ملاحظة ذكاء اصطناعي"),
                                category=af.get("category", "messaging_clarity"),
                                description=af.get("description", ""),
                                page_url=af.get("page_url", pages[0].page_url if pages else target_origin),
                                source_excerpt=af.get("source_excerpt"),
                                evidence_ids=pages[0].source_evidence_ids[:2] if pages else [],
                                observation_type="ai_interpretation",
                                severity=af.get("severity", "medium"),
                                confidence_category="inferred",
                                potential_communication_impact=af.get("potential_communication_impact"),
                            )
                        )
                    except Exception as parse_exc:
                        logger.warning("Failed to parse AI finding: %s", parse_exc)

        # 5. Evidence Validation & Quarantine
        valid_findings, quarantined_findings = ContentEvidenceValidator.validate_findings(
            findings=raw_findings,
            pages=pages,
            evidence_index=evidence_index,
        )

        # 6. Scoring
        overall_score, scores = ContentScoringEngine.calculate_scores(
            findings=valid_findings,
            pages=pages,
        )

        # 7. Recommendations
        max_recs = self.settings.content_analysis_max_recommendations
        recommendations = ContentRecommendationEngine.generate_recommendations(
            findings=valid_findings,
            max_recommendations=max_recs,
        )

        # 8. Copy Rewrite Proposals
        max_proposals = self.settings.content_analysis_max_rewrite_proposals
        rewrite_proposals = CopyProposalsEngine.generate_proposals(
            pages=pages,
            findings=valid_findings,
            max_proposals=max_proposals,
        )

        # 9. Assembly
        execution_duration = (time.time() - start_time) * 1000
        stats = ContentAnalysisStatistics(
            pages_analyzed=len(pages),
            total_words_analyzed=inventory.total_word_count,
            claims_inventoried=len(claims),
            ctas_analyzed=ctas.total_ctas_observed,
            findings_count=len(valid_findings),
            recommendations_count=len(recommendations),
            rewrite_proposals_count=len(rewrite_proposals),
            model_calls_count=model_calls,
            model_name=self.settings.content_analysis_model,
            execution_duration_ms=round(execution_duration, 1),
            ai_status=ai_status,
        )

        report = ContentMarketingReport(
            analysis_run_id=run_id,
            crawl_run_id=request.crawl_run_id,
            visual_run_id=request.visual_run_id,
            target_origin=target_origin,
            analysis_status=ai_status,
            overall_score=overall_score,
            scores=scores,
            content_inventory=inventory,
            value_proposition=value_prop,
            messaging=messaging,
            services_and_products=services,
            ctas=ctas,
            trust_and_claims=claims,
            brand_voice=voice,
            content_gaps=content_gaps,
            findings=valid_findings,
            quarantined_findings=quarantined_findings,
            recommendations=recommendations,
            rewrite_proposals=rewrite_proposals,
            statistics=stats,
        )

        # 10. Persist artifacts if requested
        if request.save_results and self.settings.content_analysis_save_results:
            ContentReportBuilder.save_artifacts(
                report=report,
                evidence_index=evidence_index,
                base_dir=str(self.base_dir),
            )

        logger.info(
            "Completed content marketing analysis %s: score=%s, status=%s in %.1fms",
            run_id,
            overall_score,
            ai_status,
            execution_duration,
        )
        return report

    analyze = analyze_content
