"""Technical SEO and Performance Analysis Service."""

import time
import uuid
from typing import Any, Optional

from site_dna.analysis.technical_seo.canonical_analyzer import CanonicalAnalyzer
from site_dna.analysis.technical_seo.context_builder import TechnicalSEOContextBuilder
from site_dna.analysis.technical_seo.core_web_vitals import CoreWebVitalsAnalyzer
from site_dna.analysis.technical_seo.crawlability import CrawlabilityAnalyzer
from site_dna.analysis.technical_seo.evidence_validator import TechnicalSEOEvidenceValidator
from site_dna.analysis.technical_seo.external_metrics import ExternalMetricsAdapter
from site_dna.analysis.technical_seo.indexability import IndexabilityAnalyzer
from site_dna.analysis.technical_seo.internal_links import InternalLinksAnalyzer
from site_dna.analysis.technical_seo.international_seo import InternationalSEOAnalyzer
from site_dna.analysis.technical_seo.javascript_seo import JavaScriptSEOAnalyzer
from site_dna.analysis.technical_seo.metadata_analyzer import MetadataAnalyzer
from site_dna.analysis.technical_seo.mobile_seo import MobileSEOAnalyzer
from site_dna.analysis.technical_seo.multimodal_adapter import TechnicalSEOMultimodalAdapter
from site_dna.analysis.technical_seo.performance import PerformanceAnalyzer
from site_dna.analysis.technical_seo.recommendations import TechnicalSEORecommendationEngine
from site_dna.analysis.technical_seo.redirect_analyzer import RedirectAnalyzer
from site_dna.analysis.technical_seo.report_builder import TechnicalSEOReportBuilder
from site_dna.analysis.technical_seo.robots_analyzer import RobotsAnalyzer
from site_dna.analysis.technical_seo.scoring import TechnicalSEOScoringEngine
from site_dna.analysis.technical_seo.sitemap_analyzer import SitemapAnalyzer
from site_dna.analysis.technical_seo.structured_data import StructuredDataAnalyzer
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.technical_seo import (
    TechnicalSEOAnalysisRequest,
    TechnicalSEOFinding,
    TechnicalSEOReport,
    TechnicalSEOStatistics,
)

logger = get_logger("analysis.technical_seo.service")


class TechnicalSEOAnalysisService:
    """Orchestrates comprehensive Technical SEO, Performance, and Core Web Vitals auditing."""

    def __init__(self, settings: Optional[Settings] = None, base_dir: str = "runs"):
        self.settings = settings or get_settings()
        self.base_dir = base_dir
        self.context_builder = TechnicalSEOContextBuilder(base_dir=base_dir)
        self.multimodal_adapter = TechnicalSEOMultimodalAdapter(settings=self.settings)
        self.external_adapter = ExternalMetricsAdapter(settings=self.settings)

    def analyze_technical_seo(
        self,
        request: TechnicalSEOAnalysisRequest,
        offline_mode: bool = False,
    ) -> TechnicalSEOReport:
        """Alias for analyze adhering to naming convention of previous analysis services."""
        if offline_mode:
            request.offline_mode = True
        return self.analyze(request)

    def analyze(
        self,
        request: TechnicalSEOAnalysisRequest,
        offline_mode: bool = False,
        **kwargs: Any,
    ) -> TechnicalSEOReport:
        """Execute complete Technical SEO and performance audit routine."""
        if offline_mode:
            request.offline_mode = True
        start_time = time.time()
        analysis_run_id = f"seo-{uuid.uuid4().hex[:12]}"

        logger.info(
            "Starting Technical SEO audit [%s] for crawl_run_id=%s",
            analysis_run_id,
            request.crawl_run_id,
        )

        # 1. Build context
        pages, crawl_result, visual_result, evidence_index = self.context_builder.build_context(
            crawl_run_id=request.crawl_run_id,
            visual_run_id=request.visual_run_id,
            max_pages=request.max_pages,
        )

        target_origin = crawl_result.website_info.canonical_origin or "https://unknown.target"
        all_raw_findings: list[TechnicalSEOFinding] = []

        # 2. Crawlability
        crawlability_res, crw_findings = CrawlabilityAnalyzer.analyze(pages, crawl_result)
        all_raw_findings.extend(crw_findings)

        # 3. Indexability
        indexability_res, idx_findings = IndexabilityAnalyzer.analyze(pages)
        all_raw_findings.extend(idx_findings)

        # 4. Robots.txt
        robots_res, rob_findings = RobotsAnalyzer.analyze(pages, crawl_result)
        all_raw_findings.extend(rob_findings)

        # 5. Sitemaps
        sitemap_res, sit_findings = SitemapAnalyzer.analyze(pages, crawl_result)
        all_raw_findings.extend(sit_findings)

        # 6. Canonical URLs
        canonical_res, can_findings = CanonicalAnalyzer.analyze(pages)
        all_raw_findings.extend(can_findings)

        # 7. Redirects
        redirect_res, red_findings = RedirectAnalyzer.analyze(pages)
        all_raw_findings.extend(red_findings)

        # 8. Metadata
        metadata_res, met_findings = MetadataAnalyzer.analyze(pages)
        all_raw_findings.extend(met_findings)

        # 9. Structured Data
        struct_res, str_findings = StructuredDataAnalyzer.analyze(pages)
        all_raw_findings.extend(str_findings)

        # 10. Internal Links
        lnk_findings = InternalLinksAnalyzer.analyze(pages)
        all_raw_findings.extend(lnk_findings)

        # 11. JavaScript SEO
        js_seo_res, js_findings = JavaScriptSEOAnalyzer.analyze(pages, visual_result)
        all_raw_findings.extend(js_findings)

        # 12. Mobile SEO
        mob_seo_res, mob_findings = MobileSEOAnalyzer.analyze(pages, visual_result)
        all_raw_findings.extend(mob_findings)

        # 13. International SEO
        intl_seo_res, intl_findings = InternationalSEOAnalyzer.analyze(pages)
        all_raw_findings.extend(intl_findings)

        # 14. Performance
        perf_measurements, perf_findings = PerformanceAnalyzer.analyze(pages, crawl_result, visual_result)
        all_raw_findings.extend(perf_findings)

        # 15. Core Web Vitals
        cwv_record, cwv_findings = CoreWebVitalsAnalyzer.analyze(pages, visual_result)
        all_raw_findings.extend(cwv_findings)

        # 16. External Metrics
        ext_metrics = self.external_adapter.fetch_metrics(target_origin)

        # 17. AI Multimodal Interpretation
        ai_status = "completed"
        model_calls_count = 0
        ai_data = None

        if not request.offline_mode and not request.deterministic_only:
            ai_data, ai_status, _ = self.multimodal_adapter.interpret_technical_seo(
                pages=pages,
                target_origin=target_origin,
                offline_mode=False,
            )
            model_calls_count = 1

            if ai_data and isinstance(ai_data, dict):
                # Incorporate AI findings
                ai_findings_raw = ai_data.get("technical_findings", [])
                for idx, aif in enumerate(ai_findings_raw[:5], 1):
                    all_raw_findings.append(
                        TechnicalSEOFinding(
                            finding_id=f"TS-AI{idx:02d}",
                            title=aif.get("title", "Technical SEO Observation"),
                            category=aif.get("category", "crawlability"),
                            description=aif.get("description", "AI detected technical observation."),
                            page_url=aif.get("page_url", pages[0].requested_url),
                            source_excerpt=aif.get("source_excerpt"),
                            evidence_ids=pages[0].source_evidence_ids[:2],
                            observation_type="ai_interpretation",
                            severity=aif.get("severity", "medium"),
                            confidence_category="inferred",
                            potential_technical_impact="التأثير على تجربة الزوار أو فاعلية الفهرسة.",
                            recommended_action=aif.get("recommended_action", "مراجعة الضوابط التقنية الموصى بها."),
                        )
                    )

        # 18. Evidence validation
        validated_findings, quarantined_findings = TechnicalSEOEvidenceValidator.validate_findings(
            findings=all_raw_findings,
            pages=pages,
            evidence_index=evidence_index,
        )

        # 19. Scoring
        overall_score, scores = TechnicalSEOScoringEngine.calculate_scores(
            pages=pages,
            findings=validated_findings,
            performance_measured=bool(perf_measurements),
        )

        # 20. Recommendations
        recommendations = TechnicalSEORecommendationEngine.generate_recommendations(
            findings=validated_findings,
            max_recommendations=self.settings.technical_seo_max_recommendations,
        )

        total_duration_ms = round((time.time() - start_time) * 1000, 2)

        statistics = TechnicalSEOStatistics(
            pages_evaluated=len(pages),
            pages_eligible=len(crawl_result.pages),
            indexing_signals_count=sum(len(p.robots_directives) for p in pages) + len(pages),
            structured_data_count=struct_res.total_schemas_found,
            performance_measurements_count=len(perf_measurements),
            field_metrics_available=False,
            lab_metrics_available=bool(perf_measurements),
            validated_findings_count=len(validated_findings),
            quarantined_findings_count=len(quarantined_findings),
            recommendations_count=len(recommendations),
            model_calls_count=model_calls_count,
            model_name=self.settings.technical_seo_model,
            execution_duration_ms=total_duration_ms,
            ai_status=ai_status,
        )

        # Determine analysis status
        analysis_status = "completed"
        if ai_status == "ai_blocked":
            analysis_status = (
                "ai_blocked" if self.settings.technical_seo_require_ai and not request.deterministic_only else "partial"
            )

        report = TechnicalSEOReport(
            schema_version="1.0",
            analysis_run_id=analysis_run_id,
            crawl_run_id=request.crawl_run_id,
            visual_run_id=request.visual_run_id,
            target_origin=target_origin,
            analysis_status=analysis_status,
            overall_score=overall_score,
            scores=scores,
            crawlability=crawlability_res,
            indexability=indexability_res,
            robots=robots_res,
            sitemap=sitemap_res,
            canonical=canonical_res,
            redirects=redirect_res,
            metadata=metadata_res,
            structured_data=struct_res,
            javascript_seo=js_seo_res,
            mobile_seo=mob_seo_res,
            international_seo=intl_seo_res,
            performance=perf_measurements,
            core_web_vitals=cwv_record,
            external_metrics=ext_metrics,
            findings=validated_findings,
            recommendations=recommendations,
            statistics=statistics,
        )

        # 21. Save artifacts if requested
        if self.settings.technical_seo_save_results:
            TechnicalSEOReportBuilder.save_artifacts(
                report=report,
                evidence_index=evidence_index,
                base_dir=self.base_dir,
            )

        logger.info(
            "Technical SEO audit [%s] finished: score=%s in %.1f ms",
            analysis_run_id,
            overall_score,
            total_duration_ms,
        )
        return report
