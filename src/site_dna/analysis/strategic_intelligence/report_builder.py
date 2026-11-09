"""Arabic Strategic Report & Executive Summary Builder for Site DNA Phase 11."""

from site_dna.schemas.strategic_intelligence import StrategicIntelligenceReport


class StrategicReportBuilder:
    """Generates professional 20-section Arabic reports and executive summaries."""

    def build_report_markdown(self, report: StrategicIntelligenceReport) -> str:
        """Construct full 20-section Arabic markdown report."""
        stats = report.statistics
        cov = report.coverage

        lines = [
            "# تقرير الذكاء الاستراتيجي وتوحيد خارطة العمل — Site DNA",
            "",
            f"**الموقع المستهدف:** `{report.target_url}`  ",
            f"**معرف الجولة الأساسية:** `{report.crawl_run_id}`  ",
            f"**معرف الجولة الاستراتيجية:** `{report.strategic_run_id}`  ",
            f"**تاريخ التحليل:** `{report.analysis_timestamp}`  ",
            f"**النموذج المعتمد:** `{report.model_name}` (حالة الذكاء الاصطناعي: `{report.ai_status}`)  ",
            "",
            "> [!IMPORTANT]",
            "> **تنبيه استشاري ومنهجي:**  ",
            "> يمثل هذا التقرير تحليلاً تركيبياً موحداً يجمع نتائج وكلاء الفحص المتخصصين في خارطة طريق تنفيذية قابلة للقياس، دون ادعاء نسب أرباح تجارية أو عوائد مالية افتراضية غير مستندة لتجارب واقعية.",
            "",
            "---",
            "",
            "## 1. الملخص التنفيذي",
            "",
            f"أجرى نظام **Site DNA** تحليلاً استراتيجياً شاملاً عبر دمج نتائج **{len(cov.available_agents)} وكلاء فحص متخصصين** بنسبة تغطية بلغت **{cov.coverage_percentage}%**.",
            f"أسفرت المعالجة عن توحيد **{stats.total_raw_findings} ملاحظة أولية** إلى **{stats.unified_findings_count} مشكلة موحدة**، مع رصد **{stats.duplicate_groups_count} مجموعة مشكلات متكررة** بين الوكلاء، و**{stats.conflicts_count} تعارضات استراتيجية** تستلزم حلاً متزناً.",
            f"تم بناء خطة تنفيذية منظمة تضم **{stats.actions_count} مهمة قابلة للتطبيق** موزعة على **4 موجات تنفيذية** مع خطط تحقق واضحة.",
            "",
            "---",
            "",
            "## 2. بيانات الموقع ونطاق التقييم",
            "",
            f"- **رابط الموقع الأساسي:** {report.target_url}",
            f"- **النطاق الأساسي (Canonical Origin):** {report.canonical_origin}",
            f"- **عدد الصفحات المشمولة:** {cov.total_pages_covered} صفحة",
            f"- **معرف الفحص الابتدائي:** `{report.crawl_run_id}`",
            "",
            "---",
            "",
            "## 3. حالة الوكلاء المستخدمة",
            "",
            "| الوكيل المتخصص | المرحلة | الحالة | عدد الملاحظات | الملاحظات التقنية |",
            "|---|---|---|---|---|",
        ]

        for r in cov.agent_records:
            status_ar = {
                "completed": "مكتمل",
                "partial": "جزئي",
                "unavailable": "غير متوفر",
                "blocked": "محظور/معلق",
            }.get(r.status, r.status)
            lines.append(f"| {r.agent_name} | {r.agent_id} | {status_ar} | {r.findings_count} | {r.limitations or 'أدلة سليمة'} |")

        lines.extend([
            "",
            "---",
            "",
            "## 4. المشكلات الموحدة",
            "",
            f"تم توحيد وتبويب الملاحظات الفنية وفق نموذج موحد يضمن تتبع الأدلة الأصلية ودرجة الإلحاح:",
            "",
        ])

        for f in report.unified_findings[:8]:
            sev_badge = f"**[{f.original_severity.upper()}]**"
            lines.append(f"- {sev_badge} **{f.title_ar or f.title}** (`{f.category}`)")
            lines.append(f"  - *الوصف:* {f.description_ar or f.description}")
            lines.append(f"  - *الوكيل المصدر:* {f.source_agent} (معرف: `{f.source_finding_id}`)")

        lines.extend([
            "",
            "---",
            "",
            "## 5. المشكلات المتكررة",
            "",
            "مجموعات المشكلات التي رصدها أكثر من وكيل متخصص وتم دمجها لمنع ازدواجية الجهود:",
            "",
        ])

        if report.duplicate_groups:
            for g in report.duplicate_groups:
                lines.append(f"### {g.canonical_title_ar or g.canonical_title}")
                lines.append(f"- **سبب الدمج:** {g.deduplication_reason_ar or g.deduplication_reason}")
                lines.append(f"- **الوكلاء الراصدون:** {', '.join(g.source_agents)}")
                lines.append(f"- **الصفحات المتأثرة:** {len(g.affected_pages)} صفحة")
                lines.append("")
        else:
            lines.append("لم يتم رصد تكرارات مباشرة بين الوكلاء في هذه الجولة.\n")

        lines.extend([
            "---",
            "",
            "## 6. المشكلات المترابطة",
            "",
            "العلاقات الدلالية والاعتمادية بين عناصر التقييم المختلفة:",
            "",
        ])

        for rel in report.relationships[:6]:
            lines.append(f"- **علاقة `{rel.relationship_type}`:** {rel.description_ar or rel.description} (ثقة: {rel.confidence * 100:.0f}%)")

        lines.extend([
            "",
            "---",
            "",
            "## 7. التعارضات",
            "",
            "نقاط التباين في التوصيات بين متطلبات المجالات المختلفة والحلول المقترحة للتوفيق بينها:",
            "",
        ])

        if report.conflicts:
            for c in report.conflicts:
                lines.append(f"### {c.description_ar or c.description}")
                lines.append(f"- **نوع التعارض:** `{c.conflict_type}`")
                lines.append(f"- **الحل التوفيقي المقترح:** {c.proposed_resolution_ar or c.proposed_resolution}")
                lines.append(f"- **يتطلب مراجعة بشرية:** {'نعم' if c.manual_review_required else 'تم الحسم تلقائياً'}")
                lines.append("")
        else:
            lines.append("لا توجد تعارضات متضاربة بين توصيات الوكلاء في هذا الفحص.\n")

        lines.extend([
            "---",
            "",
            "## 8. الأسباب الجذرية المحتملة",
            "",
            "الفرضيات الهيكلية المفسرة لتكرار المشكلات عبر قوالب الموقع:",
            "",
        ])

        for rc in report.root_cause_candidates:
            lines.append(f"### {rc.title_ar or rc.title} (درجة الثقة: `{rc.confidence}`)")
            lines.append(f"- **التفسير:** {rc.description_ar or rc.description}")
            lines.append(f"- **النمط المرصود:** {rc.shared_pattern}")
            lines.append("")

        lines.extend([
            "---",
            "",
            "## 9. فرص التحسين",
            "",
            "فرص التطوير الاستراتيجي المركبة المستخلصة من تكامل مخرجات الفحص:",
            "",
        ])

        for opp in report.opportunities:
            lines.append(f"### {opp.title_ar or opp.title} (`{opp.category}`)")
            lines.append(f"- **المشكلة المرصودة:** {opp.observed_problem}")
            lines.append(f"- **الأثر الإيجابي المتوقع:** {opp.expected_type_of_benefit}")
            lines.append(f"- **الجهد التقديري:** `{opp.estimated_effort}`")
            lines.append("")

        lines.extend([
            "---",
            "",
            "## 10. منهجية تحديد الأولويات",
            "",
            "تم ترتيب الأولويات عبر نموذج خماسي الأبعاد شفاف وعادل، يبتعد تماماً عن تخمين نسب الأرباح:",
            "- **الأثر على المستخدم والأعمال (%30):** حجم العائق الذي يواجهه الزائر.",
            "- **الإلحاح التقني والأمني والتنظيمي (%25):** حساسية الثغرات ومعايير WCAG والامتثال.",
            "- **موثوقية الأدلة وقطعيتها (%20):** استناد الفحص لأدلة برمجية حتمية خالية من الشك.",
            "- **مدى الانتشار عبر الصفحات (%15):** تأثر القوالب الرئيسية والصفحة الرئيسية.",
            "- **قابلية التطبيق والجهد الهندسي (%10):** سهولة وسرعة التنفيذ مقارنة بالمكتسبات.",
            "",
            "---",
            "",
            "## 11. الأولويات العاجلة",
            "",
            "المهام ذات الأولوية P0 و P1 التي تستوجب التنفيذ في الموجة الأولى:",
            "",
        ])

        urgent_acts = [a for a in report.actions if a.priority in ("P0", "P1")]
        for ua in urgent_acts:
            lines.append(f"- **[{ua.priority}] {ua.title_ar or ua.title}** (المسؤول المقترح: `{ua.suggested_owner_role}`)")
            lines.append(f"  - *التفاصيل:* {ua.description_ar or ua.description}")

        lines.extend([
            "",
            "---",
            "",
            "## 12. خطة التنفيذ المرحلية",
            "",
            "توزيع المهام على 4 موجات عمل تصاعدية منطقياً دون تواريخ تقويمية مختلقة:",
            "",
        ])

        for w in report.waves:
            lines.append(f"### الموجة {w.wave_number}: {w.name_ar} ({w.action_count} مهام)")
            lines.append(f"*{w.description_ar}*")
            for wa in w.actions[:4]:
                lines.append(f"  - `[{wa.priority}]` {wa.title_ar or wa.title} ({wa.suggested_owner_role})")
            lines.append("")

        lines.extend([
            "---",
            "",
            "## 13. قائمة المهام التنفيذية",
            "",
            "| المعرف | المهمة التنفيذية | الأولوية | الموجة | المسؤول المقترح | الجهد | الحالة |",
            "|---|---|---|---|---|---|---|",
        ])

        for a in report.actions[:12]:
            lines.append(f"| `{a.action_id}` | {a.title_ar or a.title} | {a.priority} | {a.wave_number} | {a.suggested_owner_role} | {a.estimated_effort} | `{a.status}` |")

        lines.extend([
            "",
            "---",
            "",
            "## 14. الاعتماديات بين المهام",
            "",
            "تسلسل التنفيذ التقني وتفادي الحلقات الاعتمادية المعيقة:",
            "",
        ])

        deps_found = False
        for a in report.actions:
            if a.dependencies:
                deps_found = True
                lines.append(f"- المهمة `{a.action_id}` تعتمد على إنجاز: `{', '.join(a.dependencies)}` أولاً.")
        if not deps_found:
            lines.append("كافة المهام التنفيذية في هذه الجولة مستقلة وقابلة للتنفيذ المتوازي.\n")

        lines.extend([
            "",
            "---",
            "",
            "## 15. توزيع المسؤوليات المقترح",
            "",
            "توزيع المهام على الأدوار الوظيفية القياسية لتسهيل التفويض دون افتراض هيكل إداري مسبق:",
            "",
        ])

        roles_summary = {}
        for a in report.actions:
            roles_summary[a.suggested_owner_role] = roles_summary.get(a.suggested_owner_role, 0) + 1

        for r_name, r_cnt in sorted(roles_summary.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- **{r_name}:** {r_cnt} مهام تنفيذية")

        lines.extend([
            "",
            "---",
            "",
            "## 16. خطة التحقق بعد الإصلاح",
            "",
            "إجراءات الاختبار الصارمة للتأكد من المعالجة الفعلية وعدم تكرار الخلل:",
            "",
        ])

        for vp in report.verification_plans[:5]:
            lines.append(f"### التحقق للمهمة `{vp.action_id}` (`{vp.domain}`)")
            lines.append(f"- **طريقة التحقق:** `{vp.method}`")
            for st in vp.steps:
                lines.append(f"  - {st}")
            lines.append("")

        lines.extend([
            "---",
            "",
            "## 17. مؤشرات قياس التحسن",
            "",
            "المقاييس الموضوعية لمراقبة جودة الموقع بعد تطبيق الخطة:",
            "",
            "| المؤشر | الهدف | خط الأساس الحالي | التكرار المقترح | القيود والاعتبارات |",
            "|---|---|---|---|---|",
        ])

        for mp in report.measurement_plans:
            base_str = str(mp.baseline_value) if mp.baseline_value is not None else "غير متوفر حالياً"
            target_str = str(mp.target_value) if mp.target_value is not None else "يحدد لاحقاً"
            lines.append(f"| {mp.name_ar} | {target_str} | {base_str} | {mp.measurement_frequency} | {mp.limitations} |")

        lines.extend([
            "",
            "---",
            "",
            "## 18. القرارات التي تحتاج مراجعة بشرية",
            "",
            "النقاط التي تقتضي تدقيقاً تقديرياً أو قراراً إدارياً من أصحاب المصلحة:",
            "",
        ])

        if report.manual_reviews:
            for hr in report.manual_reviews:
                lines.append(f"### {hr.review_reason_ar}")
                lines.append(f"- **سؤال المراجعة:** {hr.question_for_reviewer_ar}")
                lines.append(f"- **الخيارات الموصى بها:**")
                for opt in hr.recommended_options:
                    lines.append(f"  - {opt}")
                lines.append("")
        else:
            lines.append("كافة توصيات هذه الخطة مبنية على أدلة قطعية ولا تتطلب مراجعة استثنائية.\n")

        lines.extend([
            "---",
            "",
            "## 19. حالة تنفيذ الخطة",
            "",
            f"- **إجمالي المهام المعتمدة:** {stats.actions_count} مهمة",
            f"- **المهام المنجزة والمحققة:** {stats.verified_actions_count} مهمة",
            f"- **سجل التدقيق:** كافة التحديثات محفوظة بصورة دائمة ومؤرخة بالمعرفات الثابتة.",
            "",
            "---",
            "",
            "## 20. حدود التقرير",
            "",
            "1. يستند التقرير حصراً إلى نتائج ومخرجات وكلاء الفحص المتوفرة لجولة الاستكشاف الحالية.",
            "2. الوكلاء غير المتوفرين أو الجزئيين لا تُفترض نتائجهم ولا تُختلق استنتاجات بالنيابة عنهم.",
            "3. الفرضيات الخاصة بالأسباب الجذرية هي استنتاجات نمطية ولا تدعي الوصول المباشر لكود المستودع الخاص للعميل.",
            "4. لا يقدم التقرير أي ضمانات مالية أو تعهدات بنسب نمو تجارية دون دراسات ميدانية موازية.",
        ])

        return "\n".join(lines)

    def build_executive_summary(self, report: StrategicIntelligenceReport) -> str:
        """Construct compact executive summary."""
        stats = report.statistics
        cov = report.coverage
        p0_p1_count = stats.actions_by_priority.get("P0", 0) + stats.actions_by_priority.get("P1", 0)

        lines = [
            f"# الملخص التنفيذي لخارطة الطريق الاستراتيجية — {report.target_url}",
            "",
            f"> أجرى نظام **Site DNA** تحليلاً توحيدياً استراتيجياً شاملاً عبر **{len(cov.available_agents)} مجالات فحص** بنسبة تغطية **{cov.coverage_percentage}%**.",
            "",
            f"- **المشكلات الموحدة:** {stats.unified_findings_count} مشكلة مستخلصة من {stats.total_raw_findings} ملاحظة أولية.",
            f"- **مجموعات التكرار المحسومة:** {stats.duplicate_groups_count} مجموعة تم توحيدها لمنع هدر الموارد.",
            f"- **التعارضات الهندسية المحلولة:** {stats.conflicts_count} تعارضات تم وضع حلول توفيقية مدروسة لها.",
            f"- **المهام التنفيذية العاجلة (P0/P1):** {p0_p1_count} مهمة ذات أولوية قصوى.",
            f"- **إجمالي المهام المجدولة:** {stats.actions_count} مهمة عبر 4 موجات تنفيذية.",
            "",
            "### التوجيه الاستراتيجي الموصى به:",
            "البدء فوراً بالموجة الأولى لمعالجة الثغرات والترويسات الأساسية وعوائق النفاذ الحرجة، تليها معالجة المكونات والقوالب المشتركة في الموجة الثانية، مما يحقق أكبر عائد على تجربة المستخدم وموثوقية المنصة بأقل جهد تشغيلي.",
        ]
        return "\n".join(lines)
