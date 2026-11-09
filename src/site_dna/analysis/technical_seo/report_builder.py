"""Markdown and JSON report builder for Technical SEO and Performance audits."""

import json
from pathlib import Path
from typing import Any

from site_dna.core.logging import get_logger
from site_dna.schemas.technical_seo import TechnicalSEOReport

logger = get_logger("analysis.technical_seo.report_builder")


class TechnicalSEOReportBuilder:
    """Renders the comprehensive 17-section Arabic Markdown report and persists structured artifacts."""

    @staticmethod
    def render_markdown(report: TechnicalSEOReport) -> str:
        """Render complete 17-section Arabic Technical SEO report."""
        created_str = report.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        overall_str = (
            f"{report.overall_score:.1f} / 100" if report.overall_score is not None else "غير محدد (Not Assessed)"
        )

        md = f"""# تقرير الفحص التقني لمحركات البحث والأداء (Technical SEO & Performance) — Site DNA
**المشروع:** Site DNA — بصمة الموقع
**المؤسسة:** أساس للذكاء الاصطناعي (ASAAS AI)
**معرف التحليل:** `{report.analysis_run_id}`
**تاريخ التقرير:** {created_str}
**نموذج الذكاء الاصطناعي:** `{report.statistics.model_name}`
**حالة التحليل:** `{report.analysis_status.upper()}`

---

## 1. الملخص التنفيذي (Executive Summary)
أظهر التدقيق التقني الشامل لمحركات البحث والأداء لموقع {report.target_origin} مؤشراً كلياً لجودة البنية التقنية قدره **{overall_str}**. شمل التدقيق فحص وتحليل {report.statistics.pages_evaluated} صفحة، مع رصد {report.statistics.validated_findings_count} مشكلة تقنية موثقة بالأدلة، وتوليد {report.statistics.recommendations_count} توصية تقنية قابلة للتنفيذ المباشر.

**الدرجة التقنية الإجمالية:** **{overall_str}**

---

## 2. معلومات الموقع ونطاق الفحص (Website Information)
- **الموقع المستهدف:** {report.target_origin}
- **معرف جولة الاستكشاف (Crawl ID):** `{report.crawl_run_id}`
- **معرف الجولة البصرية (Visual ID):** `{report.visual_run_id or "غير متوفر"}`
- **عدد الصفحات المفحوصة:** {report.statistics.pages_evaluated} صفحة
- **إشارات الفهرسة المرصودة:** {report.statistics.indexing_signals_count} إشارة
- **مخططات البيانات المنظمة:** {report.statistics.structured_data_count} مخطط
- **قياسات الأداء المسجلة:** {report.statistics.performance_measurements_count} قياس

---

## 3. إمكانية الزحف (Crawlability & Discovery)
- **حالة سماح الزحف:** `{report.crawlability.status.upper()}`
- **إجمالي الروابط الداخلية:** {report.crawlability.total_internal_links} رابط
- **الوجهات الفريدة:** {report.crawlability.unique_destinations} صفحة
- **الروابط العاطلة المرصودة (Broken Links):** {report.crawlability.broken_links_count}
- **الصفحات اليتيمة غير المربوطة (Orphaned Pages):** {report.crawlability.orphaned_pages_detected}

---

## 4. قابلية الفهرسة (Indexability Signals)
- **حالة الفهرسة المقدرة:** `{report.indexability.status}`
- **توجيهات noindex المرصودة:** {report.indexability.noindex_count}
- **استجابات X-Robots-Tag:** {report.indexability.x_robots_tag_count}
- **الإشارات المتعارضة (Conflicting Signals):** {report.indexability.conflicting_directives_count}

---

## 5. الروابط الأساسية والتحويلات (Canonical & Redirects)
- **صفحات تفتقر إلى وسم Canonical:** {report.canonical.missing_canonical_count}
- **روابط Canonical ذاتية (Self-referencing):** {report.canonical.self_referencing_count}
- **روابط Canonical تشير لنطاق خارجي:** {report.canonical.cross_domain_canonical_count}
- **إجمالي عمليات إعادة التوجيه (Redirects):** {report.redirects.redirect_count}
- **التحويل الإلزامي إلى HTTPS:** {"✅ مفعل" if report.redirects.http_to_https_transition else "⚠️ غير مفعل"}
- **حلقات التوجيه الدائرية (Redirect Loops):** {report.redirects.redirect_loops_count}

---

## 6. ملفات خريطة الموقع (XML Sitemaps)
- **حالة العثور على خريطة الموقع:** {"✅ متوفرة" if report.sitemap.sitemap_found else "⚠️ غير مكتشفة"}
- **إجمالي الروابط في الخريطة:** {report.sitemap.total_entries_count}
- **الروابط المكررة في الخريطة:** {report.sitemap.duplicate_urls_count}
- **الروابط الخارجية غير المسموح بها:** {report.sitemap.cross_origin_entries_count}
- **نسبة تطابق الصفحات المزحوفة مع الخريطة:** {report.sitemap.crawled_urls_in_sitemap} صفحة

---

## 7. بيانات الصفحات الوصفية (Metadata Structure)
- **صفحات تفتقر إلى عنوان Title:** {report.metadata.missing_title_count}
- **صفحات تفتقر إلى وصف Description:** {report.metadata.missing_description_count}
- **عناوين مكررة عبر الصفحات (Duplicate Titles):** {report.metadata.duplicate_titles_count}
- **صفحات تفتقر إلى تهيئة Viewport للجوال:** {report.metadata.missing_viewport_count}
- **صفحات تفتقر إلى سمة اللغة lang:** {report.metadata.missing_lang_count}

---

## 8. البيانات المنظمة (Structured Data & Schema.org)
- **إجمالي المخططات المرصودة:** {report.structured_data.total_schemas_found}
- **المخططات السليمة تركيبيّاً:** {report.structured_data.valid_json_count}
- **أخطاء البناء النحوي (Syntax Errors):** {report.structured_data.syntax_error_count}
- **الأنواع المكتشفة:** {", ".join(report.structured_data.schema_types) or "لا توجد"}

---

## 9. SEO الخاص بجافاسكربت (JavaScript SEO)
- **حالة التوافق بين الخادم والمتصفح:** `{report.javascript_seo.status}`
- **تغير العنوان بعد التصيير:** {"⚠️ نعم" if report.javascript_seo.title_differs else "✅ متطابق"}
- **تغير العناوين الهيكلية بعد التصيير:** {"⚠️ نعم" if report.javascript_seo.headings_differ else "✅ متطابق"}
- **محتوى معتمد كلياً على تصيير العميل (CSR):** {"⚠️ نعم" if report.javascript_seo.content_rendered_only else "✅ مسبق التوليد"}

---

## 10. SEO الخاص بالأجهزة المحمولة (Mobile Technical SEO)
- **تهيئة وسم Viewport:** {"✅ معيارية" if report.mobile_seo.viewport_configured else "⚠️ مفقودة"}
- **تطابق محتوى الجوال مع سطح المكتب:** {"✅ متطابق" if report.mobile_seo.mobile_content_parity else "⚠️ تباين"}
- **رصد تمرير أفقي مشوه (Horizontal Overflow):** {"⚠️ رُصد خلل" if report.mobile_seo.horizontal_overflow_detected else "✅ سليم"}

---

## 11. تعدد اللغات والترميز الإقليمي (International SEO)
- **لغة المستند المعلنة:** `{report.international_seo.html_lang_declared or "غير محددة"}`
- **إجمالي إشارات hreflang البديلة:** {report.international_seo.hreflang_count}
- **صحة الإشارات التبادلية (Reciprocal):** {"✅ متوافقة" if report.international_seo.reciprocal_annotations_valid else "⚠️ خلل في التبادلية"}
- **وجود بديل x-default:** {"✅ متوفر" if report.international_seo.x_default_present else "لا يوجد"}

---

## 12. أداء الموقع وسرعة الخادم (Website Performance)
| المقياس التقني | القيمة المسجلة | الوحدة | المصدر | نوع القياس |
|---|:---:|:---:|---|---|
"""
        if report.performance:
            for p in report.performance:
                md += f"| `{p.metric_name}` | **{p.value}** | `{p.unit}` | `{p.source}` | `{p.measurement_type}` |\n"
        else:
            md += "| — | لم يتم تسجيل قياسات معملية إضافية | — | — | — |\n"

        md += f"""
---

## 13. مؤشرات تجربة المستخدم الأساسية (Core Web Vitals)
- **LCP (Largest Contentful Paint):** {f"{report.core_web_vitals.lcp_ms} ms" if report.core_web_vitals.lcp_ms else "غير مسجل"} (`{report.core_web_vitals.lcp_source}`)
- **INP (Interaction to Next Paint):** {f"{report.core_web_vitals.inp_ms} ms" if report.core_web_vitals.inp_ms else "غير متوفر (يتطلب بيانات حقلية RUM)"} (`{report.core_web_vitals.inp_source}`)
- **CLS (Cumulative Layout Shift):** {report.core_web_vitals.cls if report.core_web_vitals.cls is not None else "غير مسجل"} (`{report.core_web_vitals.cls_source}`)
- **حالة التقييم الشامل:** `{report.core_web_vitals.assessment_status.upper()}`

---

## 14. التقييم التقني ومصفوفة الأبعاد (Technical SEO Rubric)
| البعد التقييمي | الوزن | الدرجة (من 100) | الحالة | التفسير والمبررات |
|---|:---:|:---:|:---:|---|
"""
        for sc in report.scores:
            score_val = f"{sc.score:.1f}" if sc.score is not None else "—"
            md += f"| **{sc.dimension_name_ar}** | {int(sc.weight * 100)}% | {score_val} | `{sc.status}` | {sc.rationale} |\n"

        md += """
---

## 15. المشكلات التقنية المكتشفة الموثقة بالأدلة (Validated Findings)
| المعرف | العنوان | الفئة | الشدة | الصفحة | الأثر المتوقع |
|---|---|---|---|---|---|
"""
        if report.findings:
            for f in report.findings:
                md += f"| `{f.finding_id}` | {f.title} | `{f.category}` | `{f.severity.upper()}` | {f.page_url} | {f.potential_technical_impact} |\n"
        else:
            md += "| — | لم يتم رصد أي مشكلات تقنية سلبية | — | — | — | — |\n"

        md += """
---

## 16. التوصيات والإصلاحات التقنية ذات الأولوية (Prioritized Recommendations)
| الأولوية | المعرف | التوصية التقنية | الجهد | الأثر | المشكلة المعالجة |
|:---:|---|---|:---:|:---:|---|
"""
        if report.recommendations:
            for r in report.recommendations:
                md += f"| **{r.priority.upper()}** | `{r.recommendation_id}` | {r.title} | `{r.estimated_effort}` | `{r.estimated_impact}` | {r.technical_problem} |\n"
        else:
            md += "| — | — | لا توجد توصيات مطلوبة حالياً | — | — | — |\n"

        md += """
---

## 17. حدود الفحص والموثوقية (Audit Boundaries & Limitations)
1. **طبيعة الفحص الاستدلالي:** الفحص مبني على الأدلة التقنية المباشرة المستخرجة من الصفحات ولا يضمن الترتيب في محركات البحث أو الفهرسة الفعلية.
2. **غياب بيانات Search Console:** لا يمكن الجزم بحالة الفهرسة الدقيقة أو وجود عقوبات يدوية دون ربط معتمد مع حساب المشرفين.
3. **القياسات المعملية مقابل الحقلية:** قياسات الأداء المسجلة تمثل ظروف الفحص المعملي للمتصفح ولا تعكس كافة تجارب المستخدمين الواقعية.
4. **مؤشر INP:** تم تصنيف مؤشر INP كغير متوفر نظراً لعدم وجود بيانات حقلية CrUX معتمدة.
"""
        return md

    @classmethod
    def save_artifacts(
        cls,
        report: TechnicalSEOReport,
        evidence_index: dict[str, Any],
        base_dir: str = "runs",
    ) -> dict[str, str]:
        """Save report.md and all 13 structured JSON artifacts to disk."""
        target_dir = Path(base_dir) / report.crawl_run_id / "analysis" / "technical-seo" / report.analysis_run_id
        target_dir.mkdir(parents=True, exist_ok=True)

        paths: dict[str, str] = {}

        # 1. report.md
        md_content = cls.render_markdown(report)
        md_file = target_dir / "report.md"
        md_file.write_text(md_content, encoding="utf-8")
        paths["report_md"] = str(md_file)
        report.report_markdown_path = str(md_file)

        # 2. analysis.json
        analysis_file = target_dir / "analysis.json"
        analysis_file.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        paths["analysis_json"] = str(analysis_file)
        report.analysis_json_path = str(analysis_file)

        # 3. Component JSON artifacts
        (target_dir / "crawlability.json").write_text(report.crawlability.model_dump_json(indent=2), encoding="utf-8")
        (target_dir / "indexability.json").write_text(report.indexability.model_dump_json(indent=2), encoding="utf-8")
        (target_dir / "canonical-audit.json").write_text(report.canonical.model_dump_json(indent=2), encoding="utf-8")
        (target_dir / "sitemap-audit.json").write_text(report.sitemap.model_dump_json(indent=2), encoding="utf-8")
        (target_dir / "metadata-audit.json").write_text(report.metadata.model_dump_json(indent=2), encoding="utf-8")
        (target_dir / "structured-data.json").write_text(
            report.structured_data.model_dump_json(indent=2), encoding="utf-8"
        )
        (target_dir / "performance.json").write_text(
            json.dumps([p.model_dump(mode="json") for p in report.performance], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (target_dir / "core-web-vitals.json").write_text(
            report.core_web_vitals.model_dump_json(indent=2), encoding="utf-8"
        )
        (target_dir / "findings.json").write_text(
            json.dumps([f.model_dump(mode="json") for f in report.findings], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (target_dir / "recommendations.json").write_text(
            json.dumps([r.model_dump(mode="json") for r in report.recommendations], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (target_dir / "evidence-index.json").write_text(
            json.dumps(evidence_index, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

        # 4. execution-summary.json
        summary = {
            "analysis_run_id": report.analysis_run_id,
            "crawl_run_id": report.crawl_run_id,
            "visual_run_id": report.visual_run_id,
            "target_origin": report.target_origin,
            "analysis_status": report.analysis_status,
            "overall_score": report.overall_score,
            "model_name": report.statistics.model_name,
            "execution_duration_ms": report.statistics.execution_duration_ms,
            "created_at": report.created_at.isoformat(),
        }
        (target_dir / "execution-summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        logger.info("Saved all Technical SEO artifacts in %s", target_dir)
        return paths
