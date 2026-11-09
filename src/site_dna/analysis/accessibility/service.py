"""Master Orchestration Service for Site DNA Phase 10 — Accessibility & WCAG 2.2 Intelligence."""

import json
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from site_dna.analysis.accessibility.accessible_names import AccessibleNameAnalyzer
from site_dna.analysis.accessibility.aria_analysis import ARIAAnalyzer
from site_dna.analysis.accessibility.automated_rules_adapter import AutomatedRulesAdapter
from site_dna.analysis.accessibility.context_builder import AccessibilityContextBuilder
from site_dna.analysis.accessibility.contrast_analysis import ContrastAnalyzer
from site_dna.analysis.accessibility.dynamic_content import DynamicContentAnalyzer
from site_dna.analysis.accessibility.evidence_validator import AccessibilityEvidenceValidator
from site_dna.analysis.accessibility.focus_management import FocusManagementAnalyzer
from site_dna.analysis.accessibility.forms_labels import FormAccessibilityAnalyzer
from site_dna.analysis.accessibility.headings_landmarks import HeadingsLandmarksAnalyzer
from site_dna.analysis.accessibility.images_and_media import ImagesMediaAnalyzer
from site_dna.analysis.accessibility.keyboard_navigation import KeyboardFocusAnalyzer
from site_dna.analysis.accessibility.language_direction import LanguageDirectionAnalyzer
from site_dna.analysis.accessibility.links_navigation import LinksNavigationAnalyzer
from site_dna.analysis.accessibility.manual_review import ManualReviewEngine
from site_dna.analysis.accessibility.recommendations import AccessibilityRecommendationEngine
from site_dna.analysis.accessibility.reflow_zoom import ReflowZoomAnalyzer
from site_dna.analysis.accessibility.report_builder import AccessibilityReportBuilder
from site_dna.analysis.accessibility.scoring import AccessibilityScoringEngine
from site_dna.analysis.accessibility.semantics import SemanticHTMLAnalyzer
from site_dna.analysis.accessibility.target_size import TargetSizeAnalyzer
from site_dna.analysis.accessibility.wcag_criteria import WCAGCriteriaMapper
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.accessibility import (
    AccessibilityAnalysisRequest,
    AccessibilityFinding,
    AccessibilityReport,
    AccessibilityStatistics,
)

logger = get_logger("analysis.accessibility.service")


class AccessibilityService:
    """Master orchestration service executing comprehensive WCAG 2.2 accessibility intelligence."""

    def __init__(self, settings: Optional[Settings] = None, base_dir: Path | str = "runs"):
        self.settings = settings or get_settings()
        self.base_dir = Path(base_dir)
        self.context_builder = AccessibilityContextBuilder(base_dir=self.base_dir, settings=self.settings)
        self.semantics_analyzer = SemanticHTMLAnalyzer()
        self.names_analyzer = AccessibleNameAnalyzer()
        self.images_analyzer = ImagesMediaAnalyzer()
        self.headings_analyzer = HeadingsLandmarksAnalyzer()
        self.links_analyzer = LinksNavigationAnalyzer()
        self.forms_analyzer = FormAccessibilityAnalyzer()
        self.keyboard_analyzer = KeyboardFocusAnalyzer()
        self.focus_mgr_analyzer = FocusManagementAnalyzer()
        self.aria_analyzer = ARIAAnalyzer()
        self.contrast_analyzer = ContrastAnalyzer()
        self.reflow_analyzer = ReflowZoomAnalyzer()
        self.target_size_analyzer = TargetSizeAnalyzer()
        self.dynamic_analyzer = DynamicContentAnalyzer()
        self.language_analyzer = LanguageDirectionAnalyzer()
        self.rules_adapter = AutomatedRulesAdapter()
        self.wcag_mapper = WCAGCriteriaMapper()
        self.manual_review_engine = ManualReviewEngine()
        self.validator = AccessibilityEvidenceValidator()
        self.scoring_engine = AccessibilityScoringEngine()
        self.recommendations_engine = AccessibilityRecommendationEngine()
        self.report_builder = AccessibilityReportBuilder()

    def _resolve_run_dir(self, crawl_run_id: str) -> Path:
        """Resolve and validate run directory with path traversal protection."""
        from site_dna.analysis.accessibility.context_builder import validate_crawl_run_id

        valid_id = validate_crawl_run_id(crawl_run_id)
        path = (self.base_dir / valid_id).resolve()
        if not str(path).startswith(str(self.base_dir.resolve())):
            raise ValueError(f"Path traversal detected: {crawl_run_id}")
        return path

    async def analyze_crawl_run(
        self,
        crawl_run_id: str,
        skip_ai: bool = True,
    ) -> AccessibilityReport:
        """Convenience method matching Phase 08-09 service API signature."""
        req = AccessibilityAnalysisRequest(
            crawl_run_id=crawl_run_id,
            deterministic_only=skip_ai,
            save_results=True,
        )
        return await self.analyze_accessibility(req)

    async def analyze_accessibility(self, request: AccessibilityAnalysisRequest) -> AccessibilityReport:
        """Run full passive, evidence-grounded accessibility audit against crawl evidence."""
        start_time = time.perf_counter()
        logger.info("Initiating Phase 10 Accessibility audit for crawl_run_id=%s", request.crawl_run_id)

        # 1. Build and validate context
        context = self.context_builder.build_context(request)
        pages = context.page_records

        # Load raw crawl dataset for deep DOM lookups
        crawl_file = self.base_dir / request.crawl_run_id / "crawl.json"
        crawl_data: dict[str, Any] = {}
        if crawl_file.exists():
            try:
                crawl_data = json.loads(crawl_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        # 2. Execute domain analyzers
        semantics_ast = self.semantics_analyzer.analyze(pages, crawl_data)
        names_records = self.names_analyzer.analyze(pages, crawl_data)
        images_ast = self.images_analyzer.analyze(pages, crawl_data)
        self.headings_analyzer.analyze(pages, crawl_data)
        self.links_analyzer.analyze(pages, crawl_data)
        forms_ast = self.forms_analyzer.analyze(pages, crawl_data)
        keyboard_ast = self.keyboard_analyzer.analyze(pages, crawl_data)
        self.focus_mgr_analyzer.analyze(pages, crawl_data)
        aria_ast = self.aria_analyzer.analyze(pages, crawl_data)
        contrast_ast = self.contrast_analyzer.analyze(pages, crawl_data)
        reflow_ast = self.reflow_analyzer.analyze(pages, crawl_data)
        target_size_ast = self.target_size_analyzer.analyze(pages, crawl_data)
        self.dynamic_analyzer.analyze(pages, crawl_data)
        language_ast = self.language_analyzer.analyze(pages, crawl_data)

        # 3. Automated rules execution
        automated_results = []
        if request.include_automated_rules and self.settings.accessibility_automated_rules_enabled:
            automated_results = self.rules_adapter.evaluate_rules(pages, crawl_data)

        # 4. Map to WCAG 2.2 Criteria
        wcag_criteria_ast = self.wcag_mapper.map_criteria(
            semantics=semantics_ast,
            images_media=images_ast,
            keyboard=keyboard_ast,
            contrast=contrast_ast,
            reflow=reflow_ast,
            target_size=target_size_ast,
            aria=aria_ast,
            forms=forms_ast,
            language=language_ast,
        )

        # 5. Synthesize Raw Findings
        raw_findings: list[AccessibilityFinding] = []
        primary_url = context.target_url

        # Missing alt images
        if images_ast.missing_alt_count > 0:
            raw_findings.append(
                AccessibilityFinding(
                    finding_id=f"fnd-img-alt-{uuid.uuid4().hex[:6]}",
                    title="Images Missing Alternative Text (alt attribute)",
                    title_ar="صور تفتقر لسمة النص البديل (alt)",
                    description=f"Observed {images_ast.missing_alt_count} images without any alt attribute.",
                    description_ar=f"تم رصد {images_ast.missing_alt_count} صورة تفتقر تماماً لسمة النص البديل alt.",
                    page_url=primary_url,
                    component_reference="img:not([alt])",
                    category="language_media",
                    wcag_criteria=["1.1.1 Non-text Content"],
                    evidence_ids=[ev for ev in images_ast.evidence_ids if "missing-alt" in ev],
                    assessment_state="confirmed_failure",
                    severity="high",
                    user_impact="Screen reader users cannot understand the image or its function.",
                    user_impact_ar="مستخدمو برامج قراءة الشاشة يسمعون أسماء الملفات دون فهم محتوى الصورة.",
                    recommended_fix="Add descriptive alt attribute for informative images or alt='' for decorative graphics.",
                    recommended_fix_ar="أضف سمة alt تحتوي على وصف دقيق للصور الإيضاحية، أو alt='' للصور التزيينية.",
                    verification_method="Inspect DOM to ensure all img elements declare an alt attribute.",
                    verification_method_ar="عاين كود HTML للتأكد من وجود سمة alt على كافة عناصر الصور.",
                )
            )

        # Unlabeled form inputs
        if forms_ast.unlabeled_inputs > 0:
            raw_findings.append(
                AccessibilityFinding(
                    finding_id=f"fnd-form-unlabeled-{uuid.uuid4().hex[:6]}",
                    title="Form Controls Missing Programmatic Labels",
                    title_ar="حقول إدخال تفتقر للتسميات البرمجية الصريحة",
                    description=f"Found {forms_ast.unlabeled_inputs} form inputs without associated <label> or aria-label.",
                    description_ar=f"تم رصد {forms_ast.unlabeled_inputs} حقل إدخال تفتقر لوسم <label> أو سمة aria-label.",
                    page_url=primary_url,
                    component_reference="input:not([aria-label])",
                    category="forms_interaction",
                    wcag_criteria=[
                        "1.3.1 Info and Relationships",
                        "3.3.2 Labels or Instructions",
                        "4.1.2 Name, Role, Value",
                    ],
                    evidence_ids=[ev for ev in forms_ast.evidence_ids if "unlabeled" in ev],
                    assessment_state="confirmed_failure",
                    severity="critical",
                    user_impact="Users relying on assistive devices cannot determine what input is expected.",
                    user_impact_ar="يعجز ذوو الإعاقة البصرية عن معرفة الغرض من الحقل عند انتقال مؤشر التركيز إليه.",
                    recommended_fix="Associate an explicit <label for='id'> or add an aria-label attribute.",
                    recommended_fix_ar="اربط كل حقل بوسم <label for='id'> صريح أو أضف سمة aria-label واضحة.",
                    verification_method="Check that clicking label focuses the input field.",
                    verification_method_ar="تأكد من انتقال مؤشر الكتابة للحقل فور النقر على التسمية التوضيحية.",
                )
            )

        # Suppressed focus outline
        if not keyboard_ast.focus_indicators_visible:
            raw_findings.append(
                AccessibilityFinding(
                    finding_id=f"fnd-kb-outline-{uuid.uuid4().hex[:6]}",
                    title="Focus Outlines Suppressed via CSS outline:none",
                    title_ar="إلغاء إطار التركيز المرئي عبر CSS outline:none",
                    description="CSS rules suppress native outline without providing a visible :focus-visible replacement.",
                    description_ar="توجد قواعد CSS تلغي مؤشر التركيز outline:none دون توفير بديل بارز للمتنقلين باللوحة.",
                    page_url=primary_url,
                    component_reference=":focus { outline: none }",
                    category="keyboard_focus",
                    wcag_criteria=["2.4.7 Focus Visible"],
                    evidence_ids=[ev for ev in keyboard_ast.evidence_ids if "outline" in ev],
                    assessment_state="confirmed_failure",
                    severity="high",
                    user_impact="Sighted keyboard navigators lose track of where they are on the page.",
                    user_impact_ar="يفقد مستخدمو لوحة المفاتيح القدرة على متابعة موضع التركيز أثناء التنقل.",
                    recommended_fix="Specify distinct :focus-visible styling with high contrast.",
                    recommended_fix_ar="خصص نمط :focus-visible واضح المعالم وذو تباين عالٍ.",
                    verification_method="Navigate with Tab key and verify crisp focus ring on all interactive elements.",
                    verification_method_ar="تنقل بزر Tab وتأكد من ظهور إطار مميز يحيط بالعناصر التفاعلية.",
                )
            )

        # Color contrast violations
        if contrast_ast.contrast_violations_aa_normal > 0 or contrast_ast.contrast_violations_aa_large > 0:
            total_cv = contrast_ast.contrast_violations_aa_normal + contrast_ast.contrast_violations_aa_large
            raw_findings.append(
                AccessibilityFinding(
                    finding_id=f"fnd-contrast-{uuid.uuid4().hex[:6]}",
                    title="Text Color Contrast Below WCAG 2.2 AA Thresholds",
                    title_ar="انخفاض نسبة تباين الألوان عن الحد الأدنى لمعايير WCAG 2.2 AA",
                    description=f"Observed {total_cv} text elements failing the minimum contrast ratio.",
                    description_ar=f"تم رصد {total_cv} عنصر نصي تنخفض نسبة تباينها عن الحد الأدنى المطلوب.",
                    page_url=primary_url,
                    component_reference="text[style*='color']",
                    category="visual_contrast",
                    wcag_criteria=["1.4.3 Contrast (Minimum)"],
                    evidence_ids=contrast_ast.evidence_ids[:5],
                    assessment_state="confirmed_failure",
                    severity="medium",
                    user_impact="Users with low vision or navigating in bright light cannot read the text.",
                    user_impact_ar="يصعب على ضعاف البصر أو متصفحي الشاشات في الضوء الساطع قراءة المحتوى.",
                    recommended_fix="Darken text or lighten background to achieve at least 4.5:1 ratio (3.0:1 for large text).",
                    recommended_fix_ar="عدل درجة اللون لتحقيق نسبة 4.5:1 للنصوص العادية و 3.0:1 للنصوص الكبيرة على الأقل.",
                    verification_method="Verify relative luminance using eyedropper calculation.",
                    verification_method_ar="احسب النسبة باستخدام معادلة الإضاءة النسبية للتأكد من تجاوز الحد المطلوب.",
                )
            )

        # 6. Validate Evidence Provenance (Anti-Hallucination)
        all_evidence_ids = (
            set(semantics_ast.evidence_ids)
            | set(images_ast.evidence_ids)
            | set(keyboard_ast.evidence_ids)
            | set(contrast_ast.evidence_ids)
            | set(reflow_ast.evidence_ids)
            | set(target_size_ast.evidence_ids)
            | set(aria_ast.evidence_ids)
            | set(forms_ast.evidence_ids)
            | set(language_ast.evidence_ids)
            | {r.evidence_id for r in automated_results}
        )
        validated_findings, rejected_findings = self.validator.validate_findings(raw_findings, all_evidence_ids)

        # 7. Generate Manual Review Tasks
        manual_tasks = self.manual_review_engine.generate_tasks(
            pages=pages,
            images_media=images_ast,
            keyboard=keyboard_ast,
            contrast=contrast_ast,
            forms=forms_ast,
        )

        # 8. Calculate Scores
        scores = self.scoring_engine.calculate_scores(
            pages=pages,
            semantics=semantics_ast,
            images_media=images_ast,
            keyboard=keyboard_ast,
            contrast=contrast_ast,
            reflow=reflow_ast,
            target_size=target_size_ast,
            forms=forms_ast,
            language=language_ast,
            findings=validated_findings,
        )

        # 9. Prioritize Recommendations
        recommendations = self.recommendations_engine.synthesize_recommendations(pages, validated_findings)

        # 10. AI Interpretation Lifecycle via CrewAI Flow
        analysis_status = "completed"
        if request.deterministic_only or not self.settings.accessibility_require_ai:
            analysis_status = "completed_deterministic_only"
        else:
            try:
                from site_dna.flows.accessibility_flow import AccessibilityFlow

                flow = AccessibilityFlow()
                ai_result = flow.run_ai_interpretation(
                    target_url=context.target_url,
                    findings=validated_findings,
                    scores=scores,
                )
                if not ai_result:
                    analysis_status = "completed_deterministic_only"
            except Exception as e:
                logger.warning("CrewAI accessibility flow skipped or blocked by quota: %s", e)
                analysis_status = "completed_deterministic_only"

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        statistics = AccessibilityStatistics(
            pages_evaluated=len(pages),
            total_elements_inspected=sum(p.interactive_elements_count + p.form_controls_count for p in pages),
            confirmed_failures_count=len([f for f in validated_findings if f.assessment_state == "confirmed_failure"]),
            potential_issues_count=len([f for f in validated_findings if f.assessment_state == "potential_issue"]),
            manual_review_tasks_count=len(manual_tasks),
            automated_rules_count=len(automated_results),
            wcag_criteria_evaluated=len(wcag_criteria_ast),
            duration_ms=duration_ms,
        )

        report = AccessibilityReport(
            accessibility_run_id=context.accessibility_run_id,
            crawl_run_id=request.crawl_run_id,
            visual_run_id=request.visual_run_id,
            ux_run_id=request.ux_run_id,
            target_url=context.target_url,
            site_origin=context.site_origin,
            analysis_status=analysis_status,  # type: ignore
            model_name=self.settings.get_effective_accessibility_model(),
            sampling=context.sampling_record,
            semantics=semantics_ast,
            accessible_names=names_records[:50],
            images_media=images_ast,
            keyboard_focus=keyboard_ast,
            contrast=contrast_ast,
            reflow_zoom=reflow_ast,
            target_size=target_size_ast,
            aria=aria_ast,
            forms=forms_ast,
            language_direction=language_ast,
            wcag_criteria=wcag_criteria_ast,
            automated_rule_results=automated_results,
            manual_review_tasks=manual_tasks,
            scores=scores,
            findings=validated_findings,
            recommendations=recommendations,
            statistics=statistics,
        )

        # 11. Persist Artifacts to Disk
        if request.save_results:
            self._save_artifacts(report)

        return report

    def _save_artifacts(self, report: AccessibilityReport) -> None:
        """Write all Phase 10 artifacts to runs/<crawl_run_id>/analysis/accessibility/<run_id>/."""
        target_dir = self.base_dir / report.crawl_run_id / "analysis" / "accessibility" / report.accessibility_run_id
        target_dir.mkdir(parents=True, exist_ok=True)

        # 1. analysis.json
        (target_dir / "analysis.json").write_text(
            report.model_dump_json(indent=2),
            encoding="utf-8",
        )

        # 2. report.md (20-section Arabic Markdown)
        md_content = self.report_builder.build_markdown_report(report)
        (target_dir / "report.md").write_text(md_content, encoding="utf-8")

        # 3. findings.json
        (target_dir / "findings.json").write_text(
            json.dumps([f.model_dump() for f in report.findings], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # 4. recommendations.json
        (target_dir / "recommendations.json").write_text(
            json.dumps([r.model_dump() for r in report.recommendations], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # 5. manual-review-tasks.json
        (target_dir / "manual-review-tasks.json").write_text(
            json.dumps([t.model_dump() for t in report.manual_review_tasks], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # 6. wcag-criteria.json
        (target_dir / "wcag-criteria.json").write_text(
            json.dumps([c.model_dump() for c in report.wcag_criteria], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # 7. execution-summary.json
        summary = {
            "accessibility_run_id": report.accessibility_run_id,
            "crawl_run_id": report.crawl_run_id,
            "target_url": report.target_url,
            "analysis_status": report.analysis_status,
            "model_name": report.model_name,
            "overall_score": report.scores.overall_score,
            "score_label": report.scores.score_label,
            "score_label_ar": report.scores.score_label_ar,
            "pages_evaluated": report.statistics.pages_evaluated,
            "confirmed_failures": report.statistics.confirmed_failures_count,
            "manual_review_tasks": report.statistics.manual_review_tasks_count,
            "duration_ms": report.statistics.duration_ms,
        }
        (target_dir / "execution-summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        logger.info("Saved Phase 10 Accessibility artifacts to %s", target_dir)
