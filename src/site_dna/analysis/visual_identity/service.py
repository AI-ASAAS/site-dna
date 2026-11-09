"""Visual identity analysis service orchestrating evidence loading, multimodal vision, and report building."""

import time
from typing import Optional
from uuid import uuid4

from site_dna.analysis.visual_identity.color_analyzer import ColorAnalyzer
from site_dna.analysis.visual_identity.consistency_analyzer import ConsistencyAnalyzer
from site_dna.analysis.visual_identity.context_builder import VisualIdentityContextBuilder
from site_dna.analysis.visual_identity.evidence_validator import EvidenceValidator
from site_dna.analysis.visual_identity.hierarchy_analyzer import HierarchyAnalyzer
from site_dna.analysis.visual_identity.image_preprocessor import ImagePreprocessor
from site_dna.analysis.visual_identity.multimodal_adapter import MultimodalAdapter
from site_dna.analysis.visual_identity.recommendations import RecommendationEngine
from site_dna.analysis.visual_identity.report_builder import ReportBuilder
from site_dna.analysis.visual_identity.scoring import ScoringEngine
from site_dna.analysis.visual_identity.typography_analyzer import TypographyAnalyzer
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.visual_identity import (
    VisualAnalysisStatistics,
    VisualCategoryAssessment,
    VisualEvidenceReference,
    VisualFinding,
    VisualIdentityAnalysisRequest,
    VisualIdentityReport,
)

logger = get_logger("analysis.visual_identity.service")


class VisualIdentityAnalysisService:
    """End-to-end service coordinating visual identity auditing, multimodal AI, and report generation."""

    def __init__(self, settings: Optional[Settings] = None, base_dir: str = "runs"):
        self.settings = settings or get_settings()
        self.context_builder = VisualIdentityContextBuilder(base_dir=base_dir)
        self.image_preprocessor = ImagePreprocessor(max_images=self.settings.visual_analysis_max_images)
        self.multimodal_adapter = MultimodalAdapter(settings=self.settings)

    def analyze_visual_identity(
        self,
        request: VisualIdentityAnalysisRequest,
        offline_mode: bool = False,
    ) -> VisualIdentityReport:
        """Execute full visual identity evaluation pipeline."""
        start_time = time.perf_counter()
        analysis_run_id = f"vi-{uuid4().hex[:12]}"
        logger.info("Starting Visual Identity Analysis: analysis_run_id=%s", analysis_run_id)

        # 1. Build and validate analysis context
        context = self.context_builder.build_context(
            visual_run_id=request.visual_run_id,
            crawl_run_id=request.crawl_run_id,
            max_pages=request.max_pages,
        )

        # 2. Prepare and budget screenshots for multimodal vision
        prepared_images = self.image_preprocessor.prepare_images(context.pages)

        # 3. Multimodal AI Analysis (via verified Gemini 3.8 Flash Vision Adapter)
        multimodal_res = self.multimodal_adapter.analyze_visual_identity(
            context=context,
            images=prepared_images,
            offline_mode=offline_mode,
        )

        # 4. Deterministic Analyzers
        color_data = ColorAnalyzer.analyze_colors(context.pages, context.evidence_index)
        typo_data = TypographyAnalyzer.analyze_typography(context.pages, context.evidence_index)
        hierarchy_data = HierarchyAnalyzer.analyze_hierarchy(context.pages, context.evidence_index)
        consistency_data = ConsistencyAnalyzer.analyze_consistency(context.pages, context.evidence_index)

        # 5. Merge findings
        raw_findings: list[VisualFinding] = []
        raw_findings.extend(color_data.get("findings", []))
        raw_findings.extend(typo_data.get("findings", []))
        raw_findings.extend(hierarchy_data.get("findings", []))
        raw_findings.extend(consistency_data.get("findings", []))

        # Add validated AI findings from multimodal response ONLY if AI analysis succeeded
        ai_completed = multimodal_res.get("ai_analysis_completed", True)
        quota_exhausted = multimodal_res.get("quota_exhausted", False)
        fallback_reason = multimodal_res.get("fallback_reason")
        from_cache = multimodal_res.get("from_cache", False)

        if ai_completed:
            for idx, ai_f in enumerate(multimodal_res.get("ai_findings", []), 1):
                raw_findings.append(
                    VisualFinding(
                        finding_id=f"FIND-AI-{idx:02d}",
                        title=ai_f.get("title", "ملاحظة بصرية من النموذج المتعدد الوسائط"),
                        category=ai_f.get("category", "branding"),
                        severity=ai_f.get("severity", "medium"),
                        confidence="high_confidence_ai",
                        finding_type="ai_interpretation",
                        page_url=context.pages[0].page_url if context.pages else context.target_origin,
                        description=ai_f.get("description", ""),
                        potential_impact=ai_f.get("potential_impact", ""),
                        suggested_action=ai_f.get("suggested_action", ""),
                        element_references=[],
                        evidence_ids=[],
                    )
                )

        # 6. Validate Evidence & Quarantine Unsupported Claims
        valid_urls = {p.page_url for p in context.pages}
        validator = EvidenceValidator(context.evidence_index, valid_urls)
        validation_summary = validator.validate_findings(raw_findings)

        # 7. Calculate Scores
        is_multipage = len(context.pages) > 1
        overall_score, score_explanations = ScoringEngine.calculate_scores(
            findings=validation_summary.validated_findings,
            is_multipage=is_multipage,
            pages_count=len(context.pages),
        )

        # 8. Generate Recommendations
        recommendations = RecommendationEngine.generate_recommendations(
            findings=validation_summary.validated_findings,
            max_recommendations=self.settings.visual_analysis_max_recommendations,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Build evidence index list
        evidence_index_records: list[VisualEvidenceReference] = []
        for ev in context.evidence_index.values():
            evidence_index_records.append(
                VisualEvidenceReference(
                    evidence_id=ev.evidence_id,
                    evidence_category=ev.evidence_category,
                    field_reference=ev.field_reference,
                    page_url=ev.page_url,
                    viewport_profile=ev.viewport_profile,
                    screenshot_reference=ev.screenshot_reference,
                )
            )

        # Build limitations statements
        limitations = [
            "التقييم يعتمد حصراً على لقطات الشاشة والبيانات المقاسة من الصفحات المستكشفة في المرحلة 03.",
            "في حال توافر صفحة واحدة، تم حجب بعد الاتساق عبر الصفحات (Cross-Page Consistency) لتجنب الدرجات المضللة.",
            "قياسات تباين الألوان (WCAG) محسوبة بدقة على العناصر ذات الألوان المصمتة وتستثني التدرجات المعقدة.",
            "النموذج يحلل الهوية المرصودة حالياً دون فرض تفضيلات جمالية شخصية أو استنتاج هوية داخلية غير معلنة.",
        ]
        if not ai_completed:
            limitations.insert(
                0,
                f"تعذر استكمال التحليل البصري بالذكاء الاصطناعي بسبب قيود مزود النموذج ({fallback_reason or 'استنفاد الحصة اليومية'}). النتائج الحالية تقتصر على الفحوص والقياسات الحتمية التي نجحت فعلياً.",
            )

        # Category assessment bundle
        category_assessment = VisualCategoryAssessment(
            color_palette_assessment=color_data,
            typography_scale_assessment=typo_data,
            visual_hierarchy_assessment=hierarchy_data,
            cross_page_consistency_assessment=consistency_data,
            responsive_visual_assessment={
                "findings_count": len(
                    [f for f in validation_summary.validated_findings if f.category == "responsive_visual"]
                )
            },
            business_context_alignment={"context": context.business_context},
        )

        stats = VisualAnalysisStatistics(
            pages_analyzed=len(context.pages),
            viewports_analyzed=sum(len(p.desktop_screenshots) + len(p.mobile_screenshots) for p in context.pages),
            screenshots_processed=len(prepared_images),
            total_findings=validation_summary.total_findings,
            validated_findings=len(validation_summary.validated_findings),
            rejected_findings=len(validation_summary.rejected_findings),
            recommendations_count=len(recommendations),
            duration_ms=round(duration_ms, 2),
            model_name=multimodal_res.get("model_name", self.settings.visual_analysis_model),
            ai_analysis_completed=ai_completed,
            from_cache=from_cache,
            quota_exhausted=quota_exhausted,
        )

        # Determine analysis status explicitly without masking AI blocks
        if offline_mode:
            analysis_status = (
                "completed" if (validation_summary.validated_findings or overall_score is not None) else "partial"
            )
        elif quota_exhausted or not ai_completed:
            analysis_status = "ai_blocked"
        else:
            analysis_status = (
                "completed" if (validation_summary.validated_findings or overall_score is not None) else "partial"
            )

        report = VisualIdentityReport(
            analysis_run_id=analysis_run_id,
            crawl_run_id=context.crawl_run_id,
            visual_run_id=context.visual_run_id,
            site_url=context.target_origin,
            model_name=stats.model_name,
            analysis_status=analysis_status,
            ai_analysis_completed=ai_completed,
            deterministic_analysis_completed=True,
            fallback_reason=fallback_reason,
            from_cache=from_cache,
            summary_arabic=multimodal_res.get("visual_summary_arabic", ""),
            summary_english=multimodal_res.get("visual_summary_english", ""),
            overall_score=overall_score,
            score_explanations=score_explanations,
            category_assessment=category_assessment,
            findings=validation_summary.validated_findings,
            rejected_findings=validation_summary.rejected_findings,
            recommendations=recommendations,
            evidence_index=evidence_index_records,
            limitations_arabic=limitations,
            statistics=stats,
        )

        # 9. Save artifacts if requested
        if request.save_results and self.settings.visual_analysis_save_results:
            ReportBuilder.save_analysis_artifacts(report)

        logger.info(
            "Visual identity analysis finished: score=%s, %d findings, %d recs in %.1f ms",
            overall_score,
            len(report.findings),
            len(report.recommendations),
            duration_ms,
        )
        return report

    def analyze_visual_identity_sync(
        self,
        request: VisualIdentityAnalysisRequest,
        offline_mode: bool = False,
    ) -> VisualIdentityReport:
        """Synchronous wrapper for VisualIdentityAnalysisService."""
        return self.analyze_visual_identity(request=request, offline_mode=offline_mode)

    analyze = analyze_visual_identity
