"""UX/UI analysis service orchestrating evidence loading, deterministic audits, Gemini 3.6 Flash multimodal vision, and report building."""

import time
from typing import Optional
from uuid import uuid4

from site_dna.analysis.ux_ui.accessibility_analyzer import AccessibilityAnalyzer
from site_dna.analysis.ux_ui.content_usability import ContentUsabilityAnalyzer
from site_dna.analysis.ux_ui.context_builder import UXContextBuilder
from site_dna.analysis.ux_ui.evidence_validator import UXEvidenceValidator
from site_dna.analysis.ux_ui.forms_analyzer import FormsAnalyzer
from site_dna.analysis.ux_ui.interaction_analyzer import InteractionAnalyzer
from site_dna.analysis.ux_ui.journey_analyzer import JourneyAnalyzer
from site_dna.analysis.ux_ui.multimodal_adapter import UXMultimodalAdapter
from site_dna.analysis.ux_ui.navigation_analyzer import NavigationAnalyzer
from site_dna.analysis.ux_ui.recommendations import UXRecommendationEngine
from site_dna.analysis.ux_ui.report_builder import UXReportBuilder
from site_dna.analysis.ux_ui.responsive_analyzer import ResponsiveAnalyzer
from site_dna.analysis.ux_ui.scoring import UXScoringEngine
from site_dna.analysis.visual_identity.image_preprocessor import ImagePreprocessor
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.ux_ui import (
    UXAnalysisRequest,
    UXAnalysisStatistics,
    UXEvidenceReference,
    UXFinding,
    UXReport,
)

logger = get_logger("analysis.ux_ui.service")


class UXAnalysisService:
    """End-to-end service coordinating UX/UI auditing, multimodal AI, and report generation."""

    def __init__(self, settings: Optional[Settings] = None, base_dir: str = "runs"):
        self.settings = settings or get_settings()
        self.base_dir = base_dir
        self.context_builder = UXContextBuilder(base_dir=base_dir)
        self.image_preprocessor = ImagePreprocessor(max_images=self.settings.ux_analysis_max_images)
        self.multimodal_adapter = UXMultimodalAdapter(settings=self.settings)

    def analyze_ux(
        self,
        request: UXAnalysisRequest,
        offline_mode: bool = False,
        deterministic_only: bool = False,
    ) -> UXReport:
        """Execute full UX/UI evaluation pipeline combining deterministic checks and Gemini 3.6 Flash multimodal vision."""
        start_time = time.perf_counter()
        analysis_run_id = f"ux-{uuid4().hex[:12]}"
        logger.info(
            "Starting UX/UI Analysis: analysis_run_id=%s, visual_run_id=%s, model=%s",
            analysis_run_id,
            request.visual_run_id,
            self.settings.ux_analysis_model,
        )

        # 1. Build and validate analysis context
        context = self.context_builder.build_context(
            visual_run_id=request.visual_run_id,
            crawl_run_id=request.crawl_run_id,
            max_pages=request.max_pages,
        )

        # 2. Prepare screenshots for multimodal vision
        prepared_images = self.image_preprocessor.prepare_images(context.pages)

        # 3. Multimodal AI Analysis (via verified Gemini 3.6 Flash Adapter)
        is_offline = offline_mode or deterministic_only
        multimodal_res = self.multimodal_adapter.analyze_ux_ui(
            context=context,
            images=prepared_images,
            offline_mode=is_offline,
        )

        ai_completed = multimodal_res.get("ai_analysis_completed", True)
        quota_exhausted = multimodal_res.get("quota_exhausted", False)
        fallback_reason = multimodal_res.get("fallback_reason")
        from_cache = multimodal_res.get("from_cache", False)

        # 4. Deterministic Analyzers across all UX dimensions
        nav_assessment = NavigationAnalyzer.analyze_navigation(context.pages, context.evidence_index)
        int_assessment = InteractionAnalyzer.analyze_interactions(context.pages, context.evidence_index)
        forms_assessment = FormsAnalyzer.analyze_forms(context.pages, context.evidence_index)
        resp_assessment = ResponsiveAnalyzer.analyze_responsive(context.pages, context.evidence_index)
        a11y_assessment = AccessibilityAnalyzer.analyze_accessibility(context.pages, context.evidence_index)
        content_assessment = ContentUsabilityAnalyzer.analyze_content(context.pages, context.evidence_index)
        journeys = JourneyAnalyzer.analyze_journeys(context.pages, context.evidence_index)

        # 5. Merge findings
        raw_findings: list[UXFinding] = []
        raw_findings.extend(nav_assessment.findings)
        raw_findings.extend(int_assessment.findings)
        raw_findings.extend(forms_assessment.findings)
        raw_findings.extend(resp_assessment.findings)
        raw_findings.extend(a11y_assessment.findings)
        raw_findings.extend(content_assessment.findings)

        # Add validated AI findings from multimodal response ONLY if AI analysis succeeded
        if ai_completed and not deterministic_only:
            for idx, ai_f in enumerate(multimodal_res.get("ai_findings", []), 1):
                raw_findings.append(
                    UXFinding(
                        finding_id=f"FIND-UX-AI-{idx:02d}",
                        title=ai_f.get("title", "ملاحظة تجربة استخدام من نموذج الذكاء الاصطناعي"),
                        category=ai_f.get("category", "interaction"),
                        severity=ai_f.get("severity", "medium"),
                        confidence="high_confidence_ai",
                        finding_type="ai_interpretation",
                        source_page=context.pages[0].page_url if context.pages else context.target_origin,
                        viewport=ai_f.get("viewport", "all"),
                        description=ai_f.get("description", ""),
                        potential_impact=ai_f.get("potential_impact", ""),
                        suggested_action=ai_f.get("suggested_action", ""),
                        element_references=ai_f.get("element_references", []),
                        evidence_ids=[],
                    )
                )

        # 6. Validate Evidence & Quarantine Unsupported Claims
        valid_urls = {p.page_url for p in context.pages}
        validator = UXEvidenceValidator(context.evidence_index, valid_urls)
        validation_summary = validator.validate_findings(raw_findings)

        # 7. Calculate Scores across 6 dimensions
        has_forms = forms_assessment.forms_detected > 0
        overall_score, score_explanations = UXScoringEngine.calculate_scores(
            findings=validation_summary.validated_findings,
            has_forms=has_forms,
            pages_count=len(context.pages),
        )

        # 8. Generate Recommendations
        recommendations = UXRecommendationEngine.generate_recommendations(
            findings=validation_summary.validated_findings,
            max_recommendations=self.settings.ux_analysis_max_recommendations,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Build evidence index records
        evidence_index_records: list[UXEvidenceReference] = []
        for ev in context.evidence_index.values():
            evidence_index_records.append(
                UXEvidenceReference(
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
            "التقييم يعتمد حصراً على الأدلة المقاسة ولقطات الشاشة المستخرجة في المرحلتين 02 و03 دون محاكاة تفاعلية مغيرة لحالة الخادم.",
            "فحوص إمكانية الوصول آلية جزئية وتغطي المعايير القابلة للبرمجة الحتمية (WCAG 2.1/2.2 AA) دون استبدال التدقيق البشري الشامل.",
            "تم تحييد بعد النماذج للمواقع الخالية تماماً من حقول الإدخال لتفادي معاقبة المواقع التعريفية دون مبرر.",
            "فحص مسارات المستخدم (User Journeys) مشتق تحليلياً من شبكة الروابط المستكشفة في حدود الصفحات المفحوصة.",
        ]
        if not ai_completed:
            limitations.insert(
                0,
                f"تعذر استكمال التحليل المعمق بالذكاء الاصطناعي بسبب قيود مزود النموذج ({fallback_reason or 'استنفاد الحصة اليومية'}). النتائج الحالية تقتصر على الفحوص والقياسات الحتمية المكتملة فعلياً.",
            )

        # Quantitative statistics
        stats = UXAnalysisStatistics(
            pages_analyzed=len(context.pages),
            viewports_analyzed=sum(len(p.desktop_screenshots) + len(p.mobile_screenshots) for p in context.pages),
            screenshots_processed=len(prepared_images),
            interactive_elements_audited=int_assessment.total_buttons + int_assessment.total_links,
            forms_audited=forms_assessment.forms_detected,
            journeys_mapped=len(journeys),
            total_findings=validation_summary.total_findings,
            validated_findings=len(validation_summary.validated_findings),
            rejected_findings=len(validation_summary.rejected_findings),
            recommendations_count=len(recommendations),
            duration_ms=round(duration_ms, 2),
            model_name=multimodal_res.get("model_name", self.settings.ux_analysis_model),
            ai_analysis_completed=ai_completed,
            from_cache=from_cache,
            quota_exhausted=quota_exhausted,
        )

        # Determine analysis status
        if is_offline:
            analysis_status = (
                "completed" if (validation_summary.validated_findings or overall_score is not None) else "partial"
            )
        elif quota_exhausted or not ai_completed:
            analysis_status = "ai_blocked"
        else:
            analysis_status = (
                "completed" if (validation_summary.validated_findings or overall_score is not None) else "partial"
            )

        summary_ar = multimodal_res.get("executive_summary_arabic")
        if not summary_ar or len(summary_ar.strip()) < 20:
            score_txt = f"{overall_score:.1f}" if overall_score is not None else "غير متاح"
            summary_ar = (
                f"أظهر تدقيق تجربة وسهولة الاستخدام لموقع {context.target_origin} مؤشراً إجمالياً قدره {score_txt}/100. "
                f"شمل التدقيق فحص {len(context.pages)} صفحة، مع رصد {len(validation_summary.validated_findings)} ملاحظة موثقة بالأدلة "
                f"وتقديم {len(recommendations)} توصية تحسين قابلة للتنفيذ المباشر."
            )

        summary_en = multimodal_res.get("executive_summary_english")
        if not summary_en or len(summary_en.strip()) < 20:
            score_txt = f"{overall_score:.1f}" if overall_score is not None else "N/A"
            summary_en = (
                f"UX/UI audit of {context.target_origin} achieved an overall usability index of {score_txt}/100. "
                f"The assessment evaluated {len(context.pages)} pages, discovering {len(validation_summary.validated_findings)} validated findings "
                f"and formulating {len(recommendations)} prioritized, actionable recommendations."
            )

        report = UXReport(
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
            summary_arabic=summary_ar,
            summary_english=summary_en,
            overall_score=overall_score,
            score_explanations=score_explanations,
            navigation_assessment=nav_assessment,
            interaction_assessment=int_assessment,
            forms_assessment=forms_assessment,
            responsive_assessment=resp_assessment,
            accessibility_assessment=a11y_assessment,
            content_assessment=content_assessment,
            user_journeys=journeys,
            findings=validation_summary.validated_findings,
            rejected_findings=validation_summary.rejected_findings,
            recommendations=recommendations,
            evidence_index=evidence_index_records,
            limitations_arabic=limitations,
            statistics=stats,
        )

        # 9. Persist artifacts if requested
        if request.save_results or self.settings.ux_analysis_save_results:
            UXReportBuilder.save_analysis_artifacts(report, base_dir=self.base_dir)

        logger.info(
            "UX/UI Analysis completed: analysis_run_id=%s, status=%s, score=%s, findings=%d, duration=%.2fms",
            analysis_run_id,
            report.analysis_status,
            report.overall_score,
            len(report.findings),
            duration_ms,
        )
        return report

    def analyze_ux_sync(
        self,
        request: UXAnalysisRequest,
        offline_mode: bool = False,
        deterministic_only: bool = False,
    ) -> UXReport:
        """Synchronous wrapper for UXAnalysisService."""
        return self.analyze_ux(request=request, offline_mode=offline_mode, deterministic_only=deterministic_only)

    analyze = analyze_ux
