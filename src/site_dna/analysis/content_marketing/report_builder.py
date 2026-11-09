"""Report builder generating professional 14-section Arabic Markdown and structured JSON artifacts."""

import json
from pathlib import Path
from typing import Any

from site_dna.core.logging import get_logger
from site_dna.schemas.content_marketing import ContentMarketingReport

logger = get_logger("analysis.content_marketing.report_builder")


class ContentReportBuilder:
    """Builds professional Arabic Markdown reports and persists structured JSON artifacts."""

    @classmethod
    def build_markdown_report(cls, report: ContentMarketingReport) -> str:
        """Construct the 14-section Arabic Markdown report."""
        overall_str = f"{report.overall_score:.1f} / 100" if report.overall_score is not None else "غير متاح"
        created_str = report.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")

        md = f"""# تقرير تحليل المحتوى والرسائل التسويقية (Content & Marketing Intelligence) — Site DNA
**المشروع:** Site DNA — بصمة الموقع
**المؤسسة:** أساس للذكاء الاصطناعي (ASAAS AI)
**معرف التحليل:** `{report.analysis_run_id}`
**تاريخ التقرير:** {created_str}
**نموذج الذكاء الاصطناعي:** `{report.statistics.model_name}`
**حالة التحليل:** `{report.analysis_status.upper()}`

---

## 1. الملخص التنفيذي (Executive Summary)
أظهر الفحص الشامل للمحتوى والرسائل التسويقية لموقع {report.target_origin} مؤشراً إجمالياً لجودة التواصل قدره **{overall_str}**. شمل التدقيق فحص وتحليل {report.statistics.pages_analyzed} صفحة، مع رصد {report.statistics.findings_count} ملاحظة موثقة بالأدلة، وتوليد {report.statistics.recommendations_count} توصية تحسين قابلة للتنفيذ المباشر، وصياغة {report.statistics.rewrite_proposals_count} مقترحاً لإعادة صياغة العناوين وعبارات الإجراء.

**الدرجة الإجمالية للمحتوى والتسويق:** **{overall_str}**

---

## 2. معلومات الموقع ونطاق الفحص (Website Information)
- **الموقع المستهدف:** {report.target_origin}
- **معرف جولة الاستكشاف (Crawl ID):** `{report.crawl_run_id}`
- **عدد الصفحات المفحوصة:** {report.statistics.pages_analyzed} صفحة
- **إجمالي الكلمات المفحوصة:** {report.statistics.total_words_analyzed} كلمة
- **عبارات اتخاذ الإجراء (CTA) المرصودة:** {report.statistics.ctas_analyzed} عنصر
- **الادعاءات الإحصائية والتسويقية المدققة:** {report.statistics.claims_inventoried} ادعاء

---

## 3. تحليل القيمة المقترحة (Value Proposition Analysis)
- **ملخص ما يقدمه الموقع:** {report.value_proposition.offering_summary or "غير محدد بوضوح"}
- **الجمهور المستهدف المكتشف:** {report.value_proposition.target_audience or "عام أو غير مصرح به"}
- **تصنيف وضوح القيمة:** `{report.value_proposition.clarity_rating}`
- **الفوائد المحورية المذكورة:** {", ".join(report.value_proposition.core_benefits) if report.value_proposition.core_benefits else "لم ترصد عبارات فوائد واضحة"}
- **المزايا التنافسية المدعاة:** {", ".join(report.value_proposition.claimed_differentiators) if report.value_proposition.claimed_differentiators else "لم ترصد نقاط تمايز معلنة"}

---

## 4. تحليل الرسائل التسويقية (Marketing Messaging Analysis)
- **العنوان الرئيسي في الواجهة:** {report.messaging.hero_headline or "غير متوفر"}
- **العنوان الفرعي المساند:** {report.messaging.hero_subheadline or "غير متوفر"}
- **وضوح الرسالة التسويقية:** `{report.messaging.headline_clarity}`
- **مستوى المصطلحات الرنانة:** `{report.messaging.jargon_level}`
- **الادعاءات المطلقة (غير المدعومة):** {report.messaging.absolute_claims_count} ادعاء

---

## 5. تحليل صفحات الخدمات والمنتجات (Product & Service Pages Content)
- **الخدمات المكتشفة:** {report.services_and_products.total_services_identified}
- **المنتجات المكتشفة:** {report.services_and_products.total_products_identified}
- **اكتمال الشرح:** `{report.services_and_products.descriptions_completeness}`
- **وضوح الخطوة التالية لطلب الخدمة:** {"✅ واضح" if report.services_and_products.next_step_clarity else "⚠️ بحاجة لتوضيح"}

---

## 6. تحليل عبارات اتخاذ الإجراء (Call-to-Action Analysis)
- **إجمالي عبارات الحث:** {report.ctas.total_ctas_observed}
- **وجود CTA رئيسي بارز في البداية:** {"✅ متوفر" if report.ctas.primary_cta_identified else "⚠️ غير متوفر"}
- **العبارات العامة المبهمة (اضغط هنا/المزيد):** {report.ctas.generic_ctas_count}
- **عناوين الـ CTA الفريدة:** {", ".join(report.ctas.unique_cta_labels[:6]) if report.ctas.unique_cta_labels else "لا توجد"}

---

## 7. المصداقية والادعاءات (Trust & Credibility Signals)
| المعرف | نص الادعاء المرصود | النوع | الصفحة المصدر | حالة التوثيق | مراجعة |
|---|---|---|---|---|:---:|
"""
        if report.trust_and_claims:
            for c in report.trust_and_claims:
                md += f"| `{c.claim_id}` | {c.claim_text} | `{c.claim_type}` | {c.page_url} | `{c.verification_status}` | {'⚠️ مطلوبة' if c.review_required else '—'} |\n"
        else:
            md += "| — | لم يتم رصد ادعاءات أرقام أو أداء إحصائي معلنة في المحتوى | — | — | — | — |\n"

        md += f"""
---

## 8. اللغة والنبرة (Language & Brand Voice)
- **النبرة المرصودة:** `{report.brand_voice.observed_tone}`
- **اللغة الأساسية:** `{report.brand_voice.primary_language.upper()}`
- **اللهجة المرصودة:** {report.brand_voice.dialect_detected or "لغة فصحى / رسمية معيارية"}
- **تعدد اللغات:** {"نعم (موقع ثنائي اللغة)" if report.brand_voice.is_bilingual else "لغة واحدة"}
- **اتساق النبرة بين الصفحات:** `{report.brand_voice.cross_page_tone_consistency}`

---

## 9. الفجوات في المحتوى (Content Gaps)
| المعرف | نوع الفجوة | الوصف | الصفحة المتأثرة | الشدة |
|---|---|---|---|---|
"""
        if report.content_gaps:
            for g in report.content_gaps:
                md += f"| `{g.gap_id}` | `{g.gap_type}` | {g.description} | {g.page_url} | `{g.severity.upper()}` |\n"
        else:
            md += "| — | لا توجد فجوات محتوى جوهرية مرصودة ضمن الصفحات المفحوصة | — | — | — |\n"

        md += """
---

## 10. التقييم العام ومؤشرات الأبعاد السبعة (Content Evaluation Rubric)
| البعد التقييمي | الوزن | الدرجة (من 100) | الحالة | التفسير والمبررات |
|---|:---:|:---:|:---:|---|
"""
        for sc in report.scores:
            sc_str = f"{sc.score:.1f}" if sc.score is not None else "—"
            md += f"| **{sc.dimension_name_ar}** | {int(sc.weight * 100)}% | {sc_str} | `{sc.status}` | {sc.rationale} |\n"

        md += """
---

## 11. المشكلات المكتشفة الموثقة بالأدلة (Validated Findings)
| المعرف | العنوان | الفئة | الشدة | الصفحة | الأثر التواصلي المتوقع |
|---|---|---|---|---|---|
"""
        if report.findings:
            for f in report.findings:
                md += f"| `{f.finding_id}` | {f.title} | `{f.category}` | `{f.severity.upper()}` | {f.page_url} | {f.potential_communication_impact or f.description} |\n"
        else:
            md += "| — | لا توجد ملاحظات سلبية موثقة | — | — | — | — |\n"

        md += """
---

## 12. التوصيات الإجرائية المحددة (Prioritized Recommendations)
| الأولوية | المعرف | عنوان التوصية | الصفحة المتأثرة | الإجراء المقترح | الجهد |
|:---:|---|---|---|---|:---:|
"""
        if report.recommendations:
            for r in report.recommendations:
                md += f"| **{r.priority.upper()}** | `{r.recommendation_id}` | {r.title} | {r.affected_page} | {r.recommended_change} | `{r.estimated_effort}` |\n"
        else:
            md += "| — | — | المحتوى متوازن ولا يتطلب توصيات عاجلة | — | — | — |\n"

        md += """
---

## 13. مقترحات إعادة الصياغة المعتمدة على الحقائق (Grounded Copy Rewrite Proposals)
> [!NOTE]
> المقترحات التالية هي **مقترحات صياغية غير منشورة** مبنية حصرياً على الحقائق المرصودة في الموقع دون اختراع أسعار أو مزايا أو أرقام وهمية.

| المعرف | العنصر المستهدف | الصياغة الأصلية | المقترح البديل | الحقائق المحفوظة | معلومات بحاجة لتأكيد العميل |
|---|---|---|---|---|---|
"""
        if report.rewrite_proposals:
            for p in report.rewrite_proposals:
                preserved = "; ".join(p.facts_preserved) if p.facts_preserved else "حقائق النص الأصلي"
                confirm = (
                    "; ".join(p.information_requiring_confirmation)
                    if p.information_requiring_confirmation
                    else "لا يوجد"
                )
                md += f"| `{p.proposal_id}` | `{p.element_type}` | {p.original_excerpt or 'غير محدد'} | **{p.proposed_replacement}** | {preserved} | {confirm} |\n"
        else:
            md += "| — | — | لا توجد مقترحات إعادة صياغة مطلوبة | — | — | — |\n"

        md += """
---

## 14. حدود التحليل ونطاق الضمانات (Analysis Scope & Limitations)
1. **الاعتماد على عينة الصفحات المستكشفة:** التحليل يقتصر على صفحات الزحف المتاحة في الجولة الحالية، ولا يعبر عن كامل صفحات الموقع إذا لم يتم زحفها بالكامل.
2. **التمييز بين الادعاء والتحقق الخارجي:** العبارات الترويجية والادعاءات الإحصائية تُسجل كما وردت في الموقع (Claim Observed) ولا تُعد معتمدة خارجياً دون وثائق مستقلة.
3. **غياب بيانات التحليلات الفعلية (Analytics):** التوصيات مبنية على المعايير الإرشادية لسهولة القراءة وكتابة التحويل (Conversion Copywriting) ولا تمثل نتائج تجارب A/B سريرية.
4. **عدم اختراع الحقائق:** كافة مقترحات الصياغة تلتزم بحفظ الحقائق المعلنة ولا تفترض أسعاراً أو أرقاماً لم تذكرها المؤسسة.
"""
        return md

    @classmethod
    def save_artifacts(
        cls,
        report: ContentMarketingReport,
        evidence_index: dict[str, Any],
        base_dir: str = "runs",
    ) -> Path:
        """Persist all 9 structured artifacts to disk and return directory path."""
        # Target directory: runs/<crawl-run-id>/analysis/content/<analysis-run-id>/
        target_dir = Path(base_dir) / report.crawl_run_id / "analysis" / "content" / report.analysis_run_id
        target_dir.mkdir(parents=True, exist_ok=True)

        # 1. report.md
        md_content = cls.build_markdown_report(report)
        md_path = target_dir / "report.md"
        md_path.write_text(md_content, encoding="utf-8")
        report.report_markdown_path = str(md_path)

        # 2. analysis.json
        analysis_json_path = target_dir / "analysis.json"
        report.analysis_json_path = str(analysis_json_path)
        analysis_json_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

        # 3. content-inventory.json
        (target_dir / "content-inventory.json").write_text(
            report.content_inventory.model_dump_json(indent=2), encoding="utf-8"
        )

        # 4. messaging-findings.json
        (target_dir / "messaging-findings.json").write_text(
            json.dumps([f.model_dump() for f in report.findings], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # 5. recommendations.json
        (target_dir / "recommendations.json").write_text(
            json.dumps([r.model_dump() for r in report.recommendations], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # 6. copy-proposals.json
        (target_dir / "copy-proposals.json").write_text(
            json.dumps([p.model_dump() for p in report.rewrite_proposals], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # 7. claims-inventory.json
        (target_dir / "claims-inventory.json").write_text(
            json.dumps([c.model_dump() for c in report.trust_and_claims], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # 8. evidence-index.json
        (target_dir / "evidence-index.json").write_text(
            json.dumps(evidence_index, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
        )

        # 9. execution-summary.json
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
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        logger.info("Saved all 9 content marketing analysis artifacts to %s", target_dir)
        return target_dir
