"""Professional Arabic Report Builder for Site DNA Phase 08 — Competitor Intelligence."""

from datetime import datetime, timezone

from site_dna.core.logging import get_logger
from site_dna.schemas.competitor_intelligence import (
    CompetitiveFinding,
    CompetitiveGap,
    CompetitiveOpportunity,
    CompetitiveRecommendation,
    CompetitiveScore,
    CompetitorAnalysisContext,
    CompetitorIntelligenceReport,
    CompetitorProfile,
    CompetitorRelevance,
    FeatureComparisonRecord,
    MessagingBenchmark,
    PricingRecord,
    TechnicalBenchmark,
    TrustAssessment,
    UXBenchmark,
    VisualBenchmark,
)

logger = get_logger("analysis.competitor_intelligence.report_builder")


class CompetitorReportBuilder:
    """Builds the comprehensive 17-section Arabic report and wraps final CompetitorIntelligenceReport."""

    def build_report(
        self,
        context: CompetitorAnalysisContext,
        relevance: list[CompetitorRelevance],
        profiles: list[CompetitorProfile],
        feature_matrix: list[FeatureComparisonRecord],
        pricing: list[PricingRecord],
        messaging: list[MessagingBenchmark],
        visuals: list[VisualBenchmark],
        ux: list[UXBenchmark],
        technical: list[TechnicalBenchmark],
        trust: list[TrustAssessment],
        gaps: list[CompetitiveGap],
        opportunities: list[CompetitiveOpportunity],
        findings: list[CompetitiveFinding],
        recommendations: list[CompetitiveRecommendation],
        scores: CompetitiveScore,
    ) -> CompetitorIntelligenceReport:
        """Construct the Arabic Markdown deliverable and consolidated report object."""
        primary = context.primary_site
        competitors = context.competitor_sites

        lines = [
            "# تقرير استخبارات المنافسين والمقارنة المعيارية الرقمية",
            "**المنظمة:** ASAAS AI — أساس للذكاء الاصطناعي  ",
            "**المشروع:** بصمة الموقع (Site DNA) — المرحلة 08  ",
            f"**تاريخ التحليل:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
            f"**الموقع المستهدف (الرئيسي):** [{primary.display_name}]({primary.url})  ",
            f"**عدد المنافسين في المقارنة:** {len(competitors)}  ",
            "**النموذج الذكي المعتمد:** `gemini-3.6-flash`  ",
            "",
            "---",
            "",
            "## 1. الملخص التنفيذي",
            f"يقدم هذا التقرير تحليلاً مقارناً وشاملاً بين الموقع المستهدف **{primary.display_name}** وعدد ({len(competitors)}) من المواقع المنافسة عبر فحص الأدلة الرقمية العامة المستخرجة من شفرة المصدر وعناصر التصيير ولقطات الشاشة ومحتوى الصفحات.",
            f"تم رصد **{len(gaps)} فجوة تنافسية** في العرض الرقمي، واشتقاق **{len(opportunities)} فرصة استراتيجية** للتميز، وصياغة **{len(recommendations)} توصية تنفيذية** مرتبة بالأثر والجهد.",
            f"المعدل المعياري التنافسي العام للموقع: **{scores.overall_score if scores.overall_score is not None else 'قيد التقييم (بيانات جزئية)'} / 100**.",
            "",
            "## 2. معلومات المواقع ونطاق الجمع",
            "| المعرف | الموقع | النطاق الأساسي | حالة الجمع | الصفحات المفحوصة |",
            "|---|---|---|---|---|",
            f"| **الرئيسي** | {primary.display_name} | `{primary.canonical_origin}` | {primary.collection_status} | {primary.pages_collected} |",
        ]

        for c in competitors:
            lines.append(
                f"| {c.site_id} | {c.display_name} | `{c.canonical_origin}` | {c.collection_status} | {c.pages_collected} |"
            )

        lines.extend(
            [
                "",
                "## 3. مدى ملاءمة المنافسين وقابلية المقارنة",
                "| المنافس | التصنيف | درجة الملاءمة | السبب ومبرر التصنيف |",
                "|---|---|---|---|",
            ]
        )

        for r in relevance:
            cat_ar = (
                "منافس مباشر"
                if r.relevance_category == "direct"
                else ("منافس غير مباشر" if r.relevance_category == "indirect" else "استكشافي / مجاور")
            )
            lines.append(f"| {r.site_id} | **{cat_ar}** | {r.relevance_score}% | {r.reason_ar} |")

        lines.extend(
            [
                "",
                "## 4. ملفات المنافسين وسمات الأعمال المرصودة",
            ]
        )

        for p in profiles:
            lines.extend(
                [
                    f"### {p.display_name} (`{p.site_id}`)",
                    f"- **الوصف:** {p.business_description_ar}",
                    f"- **فئات الخدمات المرصودة:** {', '.join(p.offering_categories)}",
                    f"- **الجمهور المستهدف المعلن:** {p.declared_audience or 'غير محدد بدقة'}",
                    f"- **القيمة المقترحة المنشورة:** {p.published_value_proposition or 'غير معلنة صراحة'}",
                    f"- **قنوات التواصل:** {', '.join(p.public_contact_channels)}",
                    "",
                ]
            )

        lines.extend(
            [
                "## 5. مقارنة المنتجات والخدمات",
                "تم استخراج وتصنيف عروض الخدمات الرقمية وفق المعايير العامة للتطبيقات والحلول السحابية.",
                "ملاحظة منهجية: اقتصار التحليل على الصفحات التي شملها الزحف، وعدم رصد خدمة لا يعني بالضرورة عدم توفرها لدى الشركة بل عدم إبرازها في العينة المفحوصة.",
                "",
                "## 6. مصفوفة المزايا التفصيلية",
                "| الميزة / القدرة | الموقع الرئيسي | حالة المنافسين | الأهمية |",
                "|---|---|---|---|",
            ]
        )

        for f in feature_matrix:
            p_status_ar = (
                "مرصود بالموقع"
                if f.primary_status == "observed_present"
                else ("مذكور في النصوص" if f.primary_status == "claimed" else "لم يرصد بالعينة")
            )
            c_summaries = []
            for c_id, c_data in f.competitor_statuses.items():
                st = c_data.get("status")
                st_ar = "مرصود" if st == "observed_present" else ("مذكور" if st == "claimed" else "لم يرصد")
                c_summaries.append(f"{c_id}: {st_ar}")
            lines.append(f"| **{f.feature_name_ar}** | {p_status_ar} | {', '.join(c_summaries)} | {f.importance} |")

        lines.extend(
            [
                "",
                "## 7. مقارنة الأسعار والباقات المعلنة",
            ]
        )

        if any(pr.amount is not None for pr in pricing):
            lines.extend(
                [
                    "| الموقع | اسم الباقة | السعر المرصود | دورة الفوترة | حالة المقارنة |",
                    "|---|---|---|---|---|",
                ]
            )
            for pr in pricing:
                amt_str = f"{pr.amount} {pr.currency}" if pr.amount is not None else "تواصل للمبيعات"
                lines.append(
                    f"| {pr.site_id} | {pr.plan_name} | {amt_str} | {pr.billing_interval or '-'} | {pr.comparability_status} |"
                )
        else:
            lines.append(
                "لم يتم العثور على أرقام أسعار معلنة صراحة لدى الأطراف المفحوصة؛ يتم الاعتماد على التسعير المخصص (Contact Sales)."
            )

        lines.extend(
            [
                "",
                "## 8. التموضع والقيمة المقترحة",
                "يوضح الجدول أدناه كيفية صياغة الوعد التسويقي والادعاءات التفضيلية لكل موقع:",
                "",
                "## 9. الرسائل التسويقية ووضوح الخطاب",
                "| محور القياس | ملاحظة الموقع الرئيسي | الفروقات الجوهرية مع المنافسين |",
                "|---|---|---|",
            ]
        )

        for m in messaging:
            lines.append(f"| **{m.dimension_ar}** | {m.primary_observation} | {m.key_difference_ar} |")

        lines.extend(
            [
                "",
                "## 10. تجربة المستخدم والهوية البصرية المقارنة",
                "- **الهوية البصرية:** تم تقييم تناسق المقاييس الطباعية، وتناغم الألوان، وتوزيع المساحات على عرض سطح المكتب الموحد (1440px).",
                "- **تجربة المستخدم (UX):** فحص سهولة الوصول لأزرار اتخاذ القرار (CTAs)، ووضوح التسلسل الهرمي للقوائم.",
                "",
                "## 11. المقارنة التقنية ومؤشرات الأداء",
                "| المؤشر التقني | الموقع الرئيسي | المنافسون | شرط المقارنة |",
                "|---|---|---|---|",
            ]
        )

        for t in technical:
            c_vals = ", ".join([f"{k}: {v}" for k, v in t.competitor_values.items() if v is not None]) or "متماثل"
            lines.append(
                f"| **{t.metric_name}** | {t.primary_value or 'سليم'} | {c_vals} | {t.measurement_condition} |"
            )

        lines.extend(
            [
                "",
                "## 12. المصداقية والادعاءات وإثبات الثقة",
                "فحص مدى اعتماد المواقع على شهادات العملاء، دراسات الحالة الموثقة، وشارات الامتثال الأمني (مثل SOC2 و GDPR و SSL).",
                "",
                "## 13. الفجوات التنافسية في العرض الرقمي",
            ]
        )

        for g in gaps:
            lines.extend(
                [
                    f"### {g.title}",
                    f"- **نوع الفجوة:** `{g.gap_type}`",
                    f"- **التفاصيل:** {g.description_ar}",
                    f"- **الأثر الاستراتيجي:** {g.strategic_implication}",
                    f"- **التحقق المطلوب:** {g.validation_required}",
                    "",
                ]
            )

        lines.extend(
            [
                "## 14. فرص التحسين والتميّز الاستراتيجي",
            ]
        )

        for o in opportunities:
            lines.extend(
                [
                    f"### {o.title_ar}",
                    f"- **المجال:** {o.opportunity_type}",
                    f"- **الإجراء المقترح:** {o.suggested_action_ar}",
                    f"- **الأثر المقدر:** {o.estimated_impact} | **الجهد:** {o.estimated_effort}",
                    "",
                ]
            )

        lines.extend(
            [
                "## 15. التقييمات المقارنة وأوزان المعايير",
                "| البعد التقييمي | الوزن النسبي | درجة الموقع الرئيسي |",
                "|---|---|---|",
            ]
        )

        dim_names = {
            "positioning": "التموضع والقيمة المقترحة",
            "product_offering": "عرض المنتجات والخدمات",
            "content_messaging": "جودة المحتوى والرسائل",
            "ux_ui": "تجربة وواجهة المستخدم",
            "visual_identity": "الهوية البصرية والاتساق",
            "technical_seo": "الأداء التقني ومؤشرات SEO",
        }

        for dim, w in scores.dimension_weights.items():
            s_val = scores.dimension_scores.get(dim)
            s_str = f"{s_val} / 100" if s_val is not None else "غير مقيم"
            lines.append(f"| {dim_names.get(dim, dim)} | {int(w * 100)}% | **{s_str}** |")

        lines.extend(
            [
                "",
                "## 16. التوصيات والأولويات التنفيذية",
                "| الأولوية | المبادرة الاستراتيجية | الأثر | الجهد | الفئة |",
                "|---|---|---|---|---|",
            ]
        )

        for rec in recommendations:
            lines.append(
                f"| **{rec.priority.upper()}** | {rec.title_ar} | {rec.impact} | {rec.effort} | {rec.category} |"
            )

        lines.extend(
            [
                "",
                "## 17. حدود التحليل والمحددات المنهجية",
                "- هذا الفحص يمثل استخبارات للمحتوى العام المتاح عبر المواقع الإلكترونية ولا يمثل دراسة سوقية داخلية أو مالية.",
                "- عدم رصد ميزة أو خدمة في العينة المفحوصة للموقع لا يثبت عدم تقديم الشركة لها داخلياً.",
                "- مقارنة الأسعار تقتصر على الأرقام المنشورة علناً ولا تتضمن التخفيضات الخاصة أو عقود المؤسسات المغلقة.",
                "- جميع التوصيات تتطلب مصادقة فرق العمل الداخلية المختصة قبل الشروع في التنفيذ.",
            ]
        )

        report_md = "\n".join(lines)

        return CompetitorIntelligenceReport(
            comparison_run_id=context.comparison_run_id,
            status="completed",
            created_at=context.primary_site.capture_timestamp,
            completed_at=datetime.now(timezone.utc).isoformat(),
            primary_site=primary,
            competitor_sites=competitors,
            relevance_assessments=relevance,
            profiles=profiles,
            feature_matrix=feature_matrix,
            pricing_comparison=pricing,
            positioning_assessments=[],
            messaging_benchmarks=messaging,
            visual_benchmarks=visuals,
            ux_benchmarks=ux,
            technical_benchmarks=technical,
            trust_assessments=trust,
            gaps=gaps,
            opportunities=opportunities,
            findings=findings,
            recommendations=recommendations,
            scores=scores,
            report_markdown=report_md,
            limitations=context.collection_limitations,
        )
