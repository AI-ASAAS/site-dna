"""Report builder generating machine-readable JSON and professional 12-section Arabic Markdown for UX/UI intelligence."""

import json
from pathlib import Path

from site_dna.core.logging import get_logger
from site_dna.schemas.ux_ui import UXReport

logger = get_logger("analysis.ux_ui.report_builder")


class UXReportBuilder:
    """Builds comprehensive JSON and Arabic Markdown reports and manages persistence for UX/UI audits."""

    @staticmethod
    def render_arabic_markdown(report: UXReport) -> str:
        """Render the complete 12-section Arabic UX/UI audit report."""
        overall_str = (
            f"{report.overall_score:.1f} / 100" if report.overall_score is not None else "غير متاح (تغطية غير كافية)"
        )

        banner = ""
        if report.analysis_status == "ai_blocked" or not report.ai_analysis_completed:
            reason = report.fallback_reason or "استنفاد الحصة اليومية لمزود الخدمة"
            banner = f"""
> [!WARNING]
> **تنبيه:** تعذر استكمال التحليل المعمق بالذكاء الاصطناعي بسبب قيود مزود النموذج ({reason}). النتائج الحالية تقتصر على الفحوص والقياسات الحتمية المكتملة فعلياً.
"""

        md = f"""# تقرير تحليل تجربة وسهولة الاستخدام (UX/UI Intelligence) — Site DNA
**المشروع:** Site DNA — بصمة الموقع
**المؤسسة:** أساس للذكاء الاصطناعي (ASAAS AI)
**معرف التحليل:** `{report.analysis_run_id}`
**تاريخ التقرير:** {report.generated_at.strftime("%Y-%m-%d %H:%M:%S")} UTC
**نموذج الذكاء الاصطناعي:** `{report.model_name}`
**حالة التحليل:** `{report.analysis_status.upper()}`
{banner}
---

## 1. الملخص التنفيذي وتجربة المستخدم الإجمالية
{report.summary_arabic}

**الدرجة الإجمالية لتجربة الاستخدام:** **{overall_str}**

---

## 2. نطاق الفحص والصفحات المفحوصة
- **رابط الموقع المستهدف:** {report.site_url}
- **معرف جولة الاستكشاف (Crawl ID):** `{report.crawl_run_id}`
- **معرف جولة الأدلة المرئية (Visual ID):** `{report.visual_run_id}`
- **عدد الصفحات المفحوصة:** {report.statistics.pages_analyzed} صفحة
- **العناصر التفاعلية المدققة:** {report.statistics.interactive_elements_audited} عنصر
- **النماذج المفحوصة:** {report.statistics.forms_audited} نموذج
- **المسارات والسيناريوهات المخططة:** {report.statistics.journeys_mapped} مسار

---

## 3. بنية التنقل وهيكل المعلومات (Navigation & Information Architecture)
- **أقصى عمق للتنقل:** {report.navigation_assessment.max_navigation_depth} مستويات
- **إجمالي الروابط المرصودة:** {report.navigation_assessment.links_count} رابط
- **الصفحات المعزولة (Isolated Pages):** {len(report.navigation_assessment.isolated_pages)} صفحة
- **عناوين الروابط المبهمة:** {len(report.navigation_assessment.ambiguous_labels)} رابط

"""
        if report.navigation_assessment.isolated_pages:
            md += "### الصفحات المعزولة المرصودة:\n"
            for op in report.navigation_assessment.isolated_pages:
                md += f"- `{op}`\n"
        else:
            md += "- لا توجد صفحات معزولة؛ هيكل الربط الشبكي متصل.\n"

        md += f"""
---

## 4. عناصر التفاعل والأزرار ونقاط الحث على اتخاذ إجراء (Interactive Controls & CTA Clarity)
- **إجمالي الأزرار المكتشفة:** {report.interaction_assessment.total_buttons}
- **إجمالي الروابط التفاعلية:** {report.interaction_assessment.total_links}
- **أزرار الحث على اتخاذ إجراء (CTA) البارزة:** {len(report.interaction_assessment.cta_candidates)}
- **العناصر التفاعلية ذات مساحات النقر الصغيرة (< 24×24px):** {len(report.interaction_assessment.small_touch_targets)}
- **عناصر التحكم التفاعلية غير المسماة (Unlabeled Controls):** {len(report.interaction_assessment.unlabeled_controls)}

---

## 5. النماذج ومدخلات المستخدم (Forms Usability & Data Entry)
- **النماذج المكتشفة:** {report.forms_assessment.forms_detected}
- **إجمالي الحقول:** {report.forms_assessment.total_fields}
- **الحقول المفتقرة لتسميات صريحة (Unlabeled Fields):** {len(report.forms_assessment.unlabeled_fields)}
- **الحقول التي تكتفي بالنص النائب كتسمية (Placeholder-only):** {len(report.forms_assessment.placeholder_only_fields)}
- **النماذج المفتقرة لزر إرسال واضح:** {len(report.forms_assessment.missing_submit_buttons)}
"""
        if report.forms_assessment.forms_detected == 0:
            md += "- *ملاحظة:* لم يتم رصد نماذج إدخال بيانات في الصفحات المستهدفة؛ عومل بعد النماذج بحياد تام دون خصم درجات.\n"

        md += f"""
---

## 6. تجربة الهواتف المحمولة والتكيف التجاوبي (Mobile UX & Responsive Adaptability)
- **الفائض الأفقي غير المرغوب فيه (Horizontal Overflow):** {"⚠️ تم رصده" if report.responsive_assessment.horizontal_overflow_detected else "✅ غير موجود (سليم)"}
- **انهيار وتكثيف قائمة التنقل للجوال:** {"✅ مطبق بنجاح" if report.responsive_assessment.mobile_navigation_collapsed else "⚠️ غير مطبق أو غير مؤكد"}
- **العناصر المقتطعة خارج إطار الرؤية:** {report.responsive_assessment.clipped_elements_count} عنصر
- **أهداف اللمس الضيقة على الجوال (< 48×48px):** {len(report.responsive_assessment.undersized_touch_targets)} هدف

---

## 7. إمكانية الوصول وسهولة الاستخدام الأساسية (Basic Accessibility & WCAG Compliance)
- **سلامة التسلسل الهرمي للعناوين (Heading Hierarchy):** {"✅ سليم ومتسلسل" if report.accessibility_assessment.heading_hierarchy_valid else "⚠️ يحتوي على قفزات غير متسلسلة"}
- **مشكلات التسميات المتاحة لقارئات الشاشة (Accessible Name):** {len(report.accessibility_assessment.accessible_name_issues)}
- **مشكلات التباين اللوني للنصوص (WCAG AA):** {len(report.accessibility_assessment.contrast_issues)}
- **العناصر القابلة للتنقل بلوحة المفاتيح:** {report.accessibility_assessment.keyboard_focusable_count} عنصر

---

## 8. قابلية قراءة المحتوى ودعم اللغة العربية (Content Readability & Arabic RTL Usability)
- **دعم الاتجاه واللغة العربية (dir="rtl" / lang="ar"):** {"✅ معلن ومدعوم" if report.content_assessment.rtl_supported else "⚠️ غير معلن أو LTR فقط"}
- **متوسط طول الفقرات:** {report.content_assessment.average_paragraph_length:.1f} كلمة
- **مؤشر قابلية المسح البصري (Scanability Score):** {report.content_assessment.scanability_score:.1f} / 100
- **إجمالي العناوين المرصودة:** {report.content_assessment.heading_count} عنوان

---

## 9. مسارات المستخدم المعتمدة وسيناريوهات التصفح (Supported User Journeys)
| معرف المسار | الهدف المقصود | صفحة البداية | صفحة الهدف | عدد الانتقالات | الحالة | نقاط الاحتكاك المرصودة |
|---|---|---|---|:---:|:---:|---|
"""
        for jrn in report.user_journeys:
            md += f"| `{jrn.journey_id}` | **{jrn.goal}** | `{jrn.starting_page}` | `{jrn.target_page}` | {jrn.transitions_count} | `{jrn.status}` | {jrn.potential_friction or 'مسار سلس'} |\n"

        md += """
---

## 10. مؤشرات التقييم ودرجات الأبعاد الستة (UX Evaluation Rubric)
| البعد التقييمي | الوزن | الدرجة (من 100) | الحالة | التفسير والمبررات |
|---|:---:|:---:|:---:|---|
"""
        for exp in report.score_explanations:
            score_txt = f"{exp.score:.1f}" if exp.score is not None else "—"
            md += f"| **{exp.dimension_name}** | {int(exp.weight * 100)}% | {score_txt} | `{exp.status}` | {exp.explanation} |\n"

        md += """
---

## 11. المشكلات والعيوب المرصودة (UX Findings & Defects)
"""
        if report.findings:
            md += (
                "| المعرف | المشكلة | الفئة | الشدة | الصفحة | التفسير والإجراء المقترح |\n|---|---|---|---|---|---|\n"
            )
            for f in report.findings:
                md += f"| `{f.finding_id}` | **{f.title}** | `{f.category}` | `{f.severity}` | `{f.source_page}` | {f.description}<br>_الإجراء:_ {f.recommended_action} |\n"
        else:
            md += "لم تُسجل مشكلات أو عيوب تجربة استخدام حرجة في النطاق المفحوص.\n"

        md += """
---

## 12. التوصيات ذات الأولوية وخارطة التحسين (Prioritized Recommendations)
"""
        if report.recommendations:
            md += "| الأولوية | المعرف | التوصية المقترحة | المكون المعني | التحسين المتوقع في التجربة | الجهد المقدر |\n|:---:|---|---|---|---|:---:|\n"
            for r in report.recommendations:
                md += f"| **{r.priority}** | `{r.recommendation_id}` | **{r.title}**<br>{r.proposed_solution} | `{r.affected_component}` | {r.expected_improvement} | `{r.estimated_effort}` |\n"
        else:
            md += "لا توجد توصيات تعديل عاجلة؛ النظام يحقق معايير الاستخدام المقبولة.\n"

        md += """
---

## 13. حدود التقييم والقيود الفنية (Technical Limitations)
"""
        for lim in report.limitations_arabic:
            md += f"- {lim}\n"

        return md

    @staticmethod
    def save_analysis_artifacts(
        report: UXReport,
        base_dir: str = "runs",
    ) -> tuple[Path, Path]:
        """Persist analysis.json, report.md, findings.json, recommendations.json,

        evidence-index.json, journey-analysis.json, and execution-summary.json
        in runs/<crawl_id>/visual/<vis_id>/analysis/ux/<analysis_id>/.
        """
        target_dir = (
            Path(base_dir)
            / report.crawl_run_id
            / "visual"
            / report.visual_run_id
            / "analysis"
            / "ux"
            / report.analysis_run_id
        )
        target_dir.mkdir(parents=True, exist_ok=True)

        json_file = target_dir / "analysis.json"
        md_file = target_dir / "report.md"
        findings_file = target_dir / "findings.json"
        recommendations_file = target_dir / "recommendations.json"
        evidence_index_file = target_dir / "evidence-index.json"
        journey_file = target_dir / "journey-analysis.json"
        summary_file = target_dir / "execution-summary.json"

        # 1. Render Markdown
        markdown_content = UXReportBuilder.render_arabic_markdown(report)
        md_file.write_text(markdown_content, encoding="utf-8")
        report.report_markdown_path = str(md_file)

        # 2. Save JSON report
        json_file.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        report.analysis_json_path = str(json_file)

        # 3. Save findings
        findings_data = [f.model_dump() for f in report.findings]
        findings_file.write_text(json.dumps(findings_data, indent=2, default=str), encoding="utf-8")

        # 4. Save recommendations
        recommendations_data = [r.model_dump() for r in report.recommendations]
        recommendations_file.write_text(json.dumps(recommendations_data, indent=2, default=str), encoding="utf-8")

        # 5. Save evidence index
        evidence_index_data = [e.model_dump() for e in report.evidence_index]
        evidence_index_file.write_text(json.dumps(evidence_index_data, indent=2, default=str), encoding="utf-8")

        # 6. Save journey analysis
        journey_data = [j.model_dump() for j in report.user_journeys]
        journey_file.write_text(json.dumps(journey_data, indent=2, default=str), encoding="utf-8")

        # 7. Save execution summary
        summary_data = {
            "analysis_run_id": report.analysis_run_id,
            "crawl_run_id": report.crawl_run_id,
            "visual_run_id": report.visual_run_id,
            "status": report.analysis_status,
            "overall_score": report.overall_score,
            "validated_findings": report.statistics.validated_findings,
            "rejected_findings": report.statistics.rejected_findings,
            "recommendations": report.statistics.recommendations_count,
            "journeys_mapped": report.statistics.journeys_mapped,
            "duration_ms": report.statistics.duration_ms,
            "model_name": report.model_name,
            "ai_analysis_completed": report.ai_analysis_completed,
            "from_cache": report.from_cache,
        }
        summary_file.write_text(json.dumps(summary_data, indent=2, default=str), encoding="utf-8")

        logger.info("Saved UX/UI analysis artifacts to %s", target_dir)
        return json_file, md_file
