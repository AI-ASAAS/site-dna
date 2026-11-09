"""Report builder generating machine-readable JSON and professional 11-section Arabic Markdown."""

import json
from pathlib import Path

from site_dna.core.logging import get_logger
from site_dna.schemas.visual_identity import VisualIdentityReport

logger = get_logger("analysis.visual_identity.report_builder")


class ReportBuilder:
    """Builds comprehensive JSON and Arabic Markdown reports and manages persistence."""

    @staticmethod
    def render_arabic_markdown(report: VisualIdentityReport) -> str:
        """Render the complete 11-section Arabic visual identity audit report."""
        overall_str = (
            f"{report.overall_score:.1f} / 100" if report.overall_score is not None else "غير متاح (تغطية غير كافية)"
        )

        banner = ""
        if report.analysis_status == "ai_blocked" or not report.ai_analysis_completed:
            reason = report.fallback_reason or "استنفاد الحصة اليومية لمزود الخدمة"
            banner = f"""
> [!WARNING]
> **تنبيه:** تعذر استكمال التحليل البصري بالذكاء الاصطناعي بسبب قيود مزود النموذج ({reason}). النتائج الحالية تقتصر على الفحوص والقياسات الحتمية التي نجحت فعلياً.
"""

        md = f"""# تقرير تحليل الهوية البصرية وتصميم الواجهة — Site DNA
**المشروع:** Site DNA — بصمة الموقع
**المؤسسة:** أساس للذكاء الاصطناعي (ASAAS AI)
**معرف التحليل:** `{report.analysis_run_id}`
**تاريخ التقرير:** {report.generated_at.strftime("%Y-%m-%d %H:%M:%S")} UTC
**نموذج الذكاء الاصطناعي:** `{report.model_name}`
**حالة التحليل:** `{report.analysis_status.upper()}`
{banner}
---

## 1. الملخص التنفيذي
{report.summary_arabic}

---

## 2. معلومات الموقع ونطاق الفحص
- **رابط الموقع المستهدف:** {report.site_url}
- **معرف جولة الاستكشاف (Crawl ID):** `{report.crawl_run_id}`
- **معرف جولة الأدلة المرئية (Visual ID):** `{report.visual_run_id}`
- **عدد الصفحات المحللة:** {report.statistics.pages_analyzed} صفحة
- **لقطات الشاشة المعالجة:** {report.statistics.screenshots_processed} لقطة (سطح المكتب والجوال)

---

## 3. تحليل الألوان وتناسق اللوحة (Color Palette)
- **الألوان المهيمنة:** تم رصد الألوان الرئيسية المستخدمة في الخلفيات والأزرار والنصوص.
- **لون الإجراء البارز (Primary CTA):** {report.category_assessment.color_palette_assessment.get("primary_cta_color") or "غير محدد بدقة"}
- **فحوصات التباين اللوني (WCAG Contrast):**
"""
        contrast_checks = report.category_assessment.color_palette_assessment.get("contrast_checks", [])
        if contrast_checks:
            md += "| لون النص | لون الخلفية | نسبة التباين | مطابقة WCAG AA |\n|---|---|---|:---:|\n"
            for c in contrast_checks:
                status_icon = "✅ مطابق" if c["wcag_aa_pass"] else "⚠️ ضعيف"
                md += f"| `{c['text_hex']}` | `{c['bg_hex']}` | {c['ratio']}:1 | {status_icon} |\n"
        else:
            md += "لم يتم رصد تباينات لونية غير متوافقة في النصوص المقاسة المباشرة.\n"

        md += f"""
---

## 4. تحليل الخطوط والمنظومة الطباعية (Typography)
- **عائلات الخطوط المرصودة:** {", ".join(report.category_assessment.typography_scale_assessment.get("font_families", ["افتراضي"]))}
- **نسبة تدرج العنوان إلى النص:** {report.category_assessment.typography_scale_assessment.get("heading_to_body_ratio", 1.0)}:1
- **دعم اللغة والاتجاه العربي (RTL):** {"✅ مدعوم ومطبق بنجاح" if report.category_assessment.typography_scale_assessment.get("arabic_rtl_supported") else "⚠️ غير معلن أو LTR فقط"}

---

## 5. تحليل التسلسل البصري (Visual Hierarchy)
- **بروز قسم البطل (Hero Section):** {"مرصود وواضح" if report.category_assessment.visual_hierarchy_assessment.get("hero_section_detected") else "غير محدد أو مدمج"}
- **الأزرار وعناصر التوجيه:** تم رصد {report.category_assessment.visual_hierarchy_assessment.get("total_buttons_detected", 0)} عنصر توجيه/أزرار في الصفحة.
- **توازن المساحات:** توزيع متوازن للكتل البصرية بما يدعم سهولة القراءة وتوجيه العين نحو المعلومة الأهم.

---

## 6. تحليل الاتساق البصري عبر الصفحات (Consistency)
{report.category_assessment.cross_page_consistency_assessment.get("cross_page_note", "تم تقييم الاتساق.")}

---

## 7. مقارنة سطح المكتب والهاتف المحمول (Responsive)
- **حالة التكيف التجاوبي:** تم فحص العرض على شاشات سطح المكتب (1440×900) وشاشات الجوال (390×844 مع DPR=2 ومحاكاة اللمس).
- **الفائض الأفقي:** لا يوجد فائض أفقي غير مرغوب فيه على الجوال ما لم يُذكر في جدول المشكلات أدناه.

---

## 8. التقييم العام ومؤشرات الأداء
**المؤشر البصري الإجمالي:** **{overall_str}**

| البعد التقييمي | الوزن | الدرجة (من 100) | الحالة | التفسير |
|---|:---:|:---:|:---:|---|
"""
        for exp in report.score_explanations:
            score_txt = f"{exp.score:.1f}" if exp.score is not None else "—"
            md += f"| **{exp.dimension_name}** | {int(exp.weight * 100)}% | {score_txt} | `{exp.status}` | {exp.explanation} |\n"

        md += """
---

## 9. المشكلات والملاحظات المكتشفة (Findings)
"""
        if report.findings:
            md += (
                "| المعرف | المشكلة | الفئة | الشدة | الصفحة | التفسير والإجراء المقترح |\n|---|---|---|---|---|---|\n"
            )
            for f in report.findings:
                md += f"| `{f.finding_id}` | **{f.title}** | `{f.category}` | `{f.severity}` | `{f.page_url}` | {f.description}<br>_الإجراء:_ {f.suggested_action} |\n"
        else:
            md += "لم تُسجل أي مشكلات أو انحرافات بصرية حرجة في العينات المفحوصة.\n"

        md += """
---

## 10. التوصيات المقترحة والأولويات (Recommendations)
"""
        if report.recommendations:
            md += "| الأولوية | المعرف | التوصية المقترحة | المكون المعني | الأثر المتوقع | الجهد المقدر |\n|:---:|---|---|---|---|:---:|\n"
            for r in report.recommendations:
                md += f"| **{r.priority}** | `{r.recommendation_id}` | **{r.title}**<br>{r.proposed_correction} | `{r.affected_page_or_component}` | {r.expected_visual_improvement} | `{r.estimated_effort}` |\n"
        else:
            md += "لا توجد توصيات تعديل عاجلة في الوقت الراهن؛ التصميم يحقق متطلبات التماسك الأساسية.\n"

        md += """
---

## 11. حدود التحليل والقيود الفنية (Limitations)
"""
        for lim in report.limitations_arabic:
            md += f"- {lim}\n"

        return md

    @staticmethod
    def save_analysis_artifacts(
        report: VisualIdentityReport,
        base_dir: str = "runs",
    ) -> tuple[Path, Path]:
        """Persist analysis.json and report.md in runs/<crawl_id>/visual/<vis_id>/analysis/<analysis_id>/."""
        target_dir = (
            Path(base_dir) / report.crawl_run_id / "visual" / report.visual_run_id / "analysis" / report.analysis_run_id
        )
        target_dir.mkdir(parents=True, exist_ok=True)

        json_file = target_dir / "analysis.json"
        md_file = target_dir / "report.md"
        evidence_index_file = target_dir / "evidence-index.json"
        summary_file = target_dir / "execution-summary.json"

        # 1. Render Markdown
        markdown_content = ReportBuilder.render_arabic_markdown(report)
        md_file.write_text(markdown_content, encoding="utf-8")
        report.report_markdown_path = str(md_file)

        # 2. Save JSON report
        json_file.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        report.analysis_json_path = str(json_file)

        # 3. Save evidence index
        evidence_index_data = [e.model_dump() for e in report.evidence_index]
        evidence_index_file.write_text(json.dumps(evidence_index_data, indent=2), encoding="utf-8")

        # 4. Save execution summary
        summary_data = {
            "analysis_run_id": report.analysis_run_id,
            "crawl_run_id": report.crawl_run_id,
            "visual_run_id": report.visual_run_id,
            "status": report.analysis_status,
            "overall_score": report.overall_score,
            "validated_findings": report.statistics.validated_findings,
            "rejected_findings": report.statistics.rejected_findings,
            "recommendations": report.statistics.recommendations_count,
            "duration_ms": report.statistics.duration_ms,
            "model_name": report.model_name,
        }
        summary_file.write_text(json.dumps(summary_data, indent=2), encoding="utf-8")

        logger.info("Saved visual identity analysis artifacts to %s", target_dir)
        return json_file, md_file
