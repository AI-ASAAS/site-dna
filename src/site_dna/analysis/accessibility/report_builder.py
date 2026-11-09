"""Bilingual Analytical Report Builder for Site DNA Phase 10 (WCAG 2.2)."""

from site_dna.schemas.accessibility import AccessibilityReport


class AccessibilityReportBuilder:
    """Generates professional Markdown audit reports in Arabic adhering to the 20 required sections."""

    def build_markdown_report(self, report: AccessibilityReport) -> str:
        """Construct comprehensive Arabic Markdown report."""
        scores = report.scores
        stats = report.statistics
        sampling = report.sampling

        confirmed_findings = [f for f in report.findings if f.assessment_state == "confirmed_failure"]
        potential_findings = [f for f in report.findings if f.assessment_state == "potential_issue"]

        lines = [
            "# تقرير تدقيق إمكانية الوصول وتجربة المستخدم الشاملة (WCAG 2.2) — Site DNA",
            "",
            f"**الموقع المستهدف:** `{report.target_url}`  ",
            f"**معرف الجولة:** `{report.accessibility_run_id}`  ",
            f"**تاريخ التدقيق:** `{report.analysis_timestamp}`  ",
            f"**النموذج الذكي المعتمد:** `{report.model_name}`  ",
            f"**حالة الفحص:** `{report.analysis_status}`  ",
            "",
            "> [!IMPORTANT]",
            "> **إخلاء مسؤولية تنظيمي وقانوني:**  ",
            f"> {scores.conformance_disclaimer_ar}",
            "",
            "---",
            "",
            "## 1. الملخص التنفيذي",
            "",
            "أجرى نظام **Site DNA (بصمة الموقع)** تقييماً دفاعياً شاملاً لإمكانية الوصول الرقمي وتجربة المستخدم الشاملة وفق إرشادات النفاذ إلى محتوى الويب العالمية **WCAG 2.2** بمستوييها **A و AA**.",
            f"- **التقييم العام المركب:** **{scores.overall_score if scores.overall_score is not None else 'غير متاح'} / 100** ({scores.score_label_ar})",
            f"- **الصفحات المفحوصة في العينة:** {stats.pages_evaluated} صفحة ممثلة.",
            f"- **المشكلات المؤكدة آلياً:** {stats.confirmed_failures_count} حاجز نفاذ مؤكد.",
            f"- **الملاحظات المحتملة:** {stats.potential_issues_count} ملاحظة استرشادية.",
            f"- **مهام المراجعة البشرية المطلوبة:** {stats.manual_review_tasks_count} مهمة تتطلب تدقيقاً يدوياً.",
            "",
            "---",
            "",
            "## 2. نطاق الفحص والعينات الممثلة",
            "",
            f"تم اختيار عينة ممثلة مكونة من **{sampling.sampled_pages_count}** صفحة من إجمالي **{sampling.total_pages_discovered}** رابط تم اكتشافه بواسطة محرك الزحف، بناءً على تنوع الكثافة التفاعلية وتواجد النماذج:",
            "",
            "| الرابط | العنوان | الدور في العينة | العناصر التفاعلية | الحقول |",
            "|---|---|---|---|---|",
        ]

        for p in sampling.sampled_pages:
            title_clean = (p.page_title or "صفحة فرعية").replace("|", "-")
            reason_clean = (p.sample_reason or "عينة عامة").replace("|", "-")
            lines.append(
                f"| `{p.page_url}` | {title_clean} | {reason_clean} | {p.interactive_elements_count} | {p.form_controls_count} |"
            )

        lines.extend(
            [
                "",
                "---",
                "",
                "## 3. المنهجية والمعايير المعتمدة",
                "",
                "- **المرجع التقني الأساسي:** W3C Web Content Accessibility Guidelines (WCAG) 2.2 (المستويات A و AA).",
                "- **منهجية التقييم:** WCAG-EM 2.0 المعتمدة دولياً.",
                "- **مستويات الأدلة:** التمييز الصارم بين الأدلة المرصودة حتمياً (Level A & B) وبين الملاحظات الاسترشادية والتفسير الذكي (Level C & D).",
                "- **حجب الهلوسة:** عدم تصنيف أي معيار على أنه متوافق كلياً بمجرد خلو الفحص الآلي من الأخطاء.",
                "",
                "---",
                "",
                "## 4. بنية الصفحات والعناصر الدلالية (Semantic HTML)",
                "",
                f"- **معلم المحتوى الرئيسي `<main>`:** {'متوفر ومحدد' if report.semantics.has_main_landmark else 'غير متوفر (حاجز بنيوي)'}.",
                f"- **معالم التنقل `<nav>`:** {report.semantics.nav_landmarks_count} معالم تنقل مسجلة.",
                f"- **تسلسل العناوين (H1-H6):** {'تسلسل متناسق دون قفزات' if report.semantics.headings_hierarchy_valid else 'يحتوي على قفزات غير دلالية في المستويات'}.",
                f"- **الأزرار الحقيقية مقابل العناصر البديلة:** نسبة الأزرار الدلالية {int(report.semantics.buttons_vs_divs_ratio * 100)}%.",
                f"- **جداول البيانات:** {report.semantics.data_tables_with_headers} جداول بترويسات صحيحة مقابل {report.semantics.unheaded_tables_count} جداول تفتقر لترويسة `<th>`.",
                "",
                "---",
                "",
                "## 5. الأسماء والوصف المتاح (Accessible Names & Labels)",
                "",
                "تم تدقيق شجرة الأسماء المتاحة وفق مبادئ **W3C AccName 1.2** عبر العناصر التفاعلية:",
                f"- إجمالي الأسماء المتاحة المفحوصة: {len(report.accessible_names)} عنصر.",
                f"- أزرار وروابط تفتقر لاسم متاح: {report.images_media.functional_icon_buttons_without_name} عنصر.",
                "",
                "---",
                "",
                "## 6. التنقل بلوحة المفاتيح (Keyboard Navigation)",
                "",
                f"- **العناصر القابلة للتركيز:** {report.keyboard_focus.focusable_elements_count} عنصر تفاعلي.",
                f"- **تسلسل التنقل المنطقي:** {'تسلسل طبيعي متسق' if report.keyboard_focus.tab_order_sequential else 'استخدام tabindex موجب يخل بالترتيب'}.",
                f"- **فخاخ التركيز (Keyboard Traps):** {report.keyboard_focus.keyboard_traps_detected} فخاخ مرصودة حتمياً.",
                f"- **رابط تجاوز التنقل (Skip Link):** {'متوفر في أعلى الصفحة' if report.keyboard_focus.skip_link_present else 'غير متوفر (يتطلب إضافة)'}.",
                "",
                "---",
                "",
                "## 7. إدارة التركيز ومؤشراته (Focus Management)",
                "",
                f"- **مؤشرات التركيز المرئية:** {'مؤشرات بارزة واضحة' if report.keyboard_focus.focus_indicators_visible else 'ملغاة عبر CSS outline:none دون بديل مرئي'}.",
                f"- **احتمالية حجب التركيز بالقوائم الثابتة (WCAG 2.4.11):** {report.keyboard_focus.focus_obscured_by_sticky_elements} عناصر قد تحجب مؤشر التحديد أثناء التمرير.",
                "",
                "---",
                "",
                "## 8. النماذج وحقول الإدخال (Forms Accessibility)",
                "",
                f"- **إجمالي حقول الإدخال:** {report.forms.total_form_inputs} حقل.",
                f"- **الحقول المرتبطة بتسمية صريحة `<label>`:** {report.forms.inputs_with_explicit_labels} حقل.",
                f"- **حقول الإدخال غير المسماة:** {report.forms.unlabeled_inputs} حقل.",
                f"- **رسائل الخطأ المرتبطة برمجياً:** {report.forms.error_messages_programmatically_associated} حقل يدعم aria-describedby.",
                f"- **اعتبارات تسجيل الدخول والمصادقة:** {'تم رصد نماذج مصادقة تتطلب التحقق من مرونة اللصق' if report.forms.has_accessible_authentication_considerations else 'لا توجد نماذج مصادقة في العينة'}.",
                "",
                "---",
                "",
                "## 9. التباين البصري للألوان (Color Contrast)",
                "",
                f"- **العناصر المقاسة حتمياً:** {report.contrast.measured_text_elements_count} عنصر نصي.",
                f"- **مخالفات تباين النصوص العادية (< 4.5:1):** {report.contrast.contrast_violations_aa_normal} عنصر.",
                f"- **مخالفات تباين النصوص الكبيرة (< 3.0:1):** {report.contrast.contrast_violations_aa_large} عنصر.",
                f"- **العناصر المطابقة لنسبة التباين:** {report.contrast.contrast_passes_count} عنصر.",
                f"- **أسوأ نسبة تباين مرصودة:** {f'{report.contrast.worst_contrast_ratio}:1' if report.contrast.worst_contrast_ratio else 'غير محددة'}.",
                "",
                "---",
                "",
                "## 10. التجاوب وإعادة التدفق (Reflow & Text Zoom)",
                "",
                f"- **التمرير ثنائي الأبعاد عند عرض 320px (WCAG 1.4.10):** {'تم رصد تمرير أفقي غير مرغوب' if report.reflow_zoom.horizontal_overflow_at_320px else 'المحتوى يتدفق رأسياً بسلاسة'}.",
                f"- **قص النصوص وحظر التكبير (WCAG 1.4.4):** {'تم رصد حظر لتكبير الشاشة أو قص نصوص بحاويات مغلقة' if report.reflow_zoom.text_clipping_observed else 'التكبير وتدفق النصوص سليم'}.",
                "",
                "---",
                "",
                "## 11. سمات ARIA والمكونات التفاعلية (WAI-ARIA)",
                "",
                f"- **أدوار ARIA المستخدمة:** {', '.join(report.aria.aria_roles_used) if report.aria.aria_roles_used else 'لا توجد أدوار إضافية'}.",
                f"- **أدوار ARIA غير الصالحة:** {len(report.aria.invalid_roles)} دور غير قياسي.",
                f"- **المعرفات المرجعية المعطوبة (Broken IDs):** {len(report.aria.broken_aria_references)} معرف معطوب.",
                f"- **سوء استخدام سمة aria-hidden:** {report.aria.misused_aria_hidden} عنصر تفاعلي تم إخفاؤه خطأً عن قارئات الشاشة.",
                "",
                "---",
                "",
                "## 12. العربية وتعدد اللغات واتجاه الواجهة (RTL / Language)",
                "",
                f"- **إعلان لغة المستند `<html lang>`:** {'معلن بشكل صحيح' if report.language_direction.html_lang_declared else 'مفقود (يتسبب في نطق خاطئ من برامج القراءة)'}.",
                f"- **اللغة المعلنة:** `{report.language_direction.declared_language or 'غير محددة'}`  ",
                f"- **اتجاه النص المعلن:** `{report.language_direction.declared_direction or 'غير محدد'}`  ",
                f"- **دعم الواجهة ثنائية اللغة:** {'تم رصد محول للغات' if report.language_direction.bilingual_arabic_english_support else 'أحادية اللغة'}.",
                f"- **عزل النصوص الأجنبية المضمنة:** {'نصوص إنجليزية معزولة' if report.language_direction.mixed_direction_spans_isolated else 'توجد نصوص إنجليزية غير محددة السمة مما يربك القارئ الآلي'}.",
                "",
                "---",
                "",
                "## 13. الوسائط والمحتوى غير النصي (Media & Non-Text)",
                "",
                f"- **إجمالي الصور المفحوصة:** {report.images_media.total_images} صورة.",
                f'- **صور تزيينية بنص بديل فارغ سليم (`alt=""`):** {report.images_media.decorative_images_count} صورة.',
                f"- **صور إيضاحية بنص بديل:** {report.images_media.informative_images_count} صورة.",
                f"- **صور تفتقر لسمة alt بالكامل:** {report.images_media.missing_alt_count} صورة.",
                f"- **مقاطع الفيديو المرصودة:** {report.images_media.videos_count} فيديو (منها {report.images_media.videos_with_captions_observed} بملفات ترجمة نصية).",
                "",
                "---",
                "",
                "## 14. جدول الربط بمعايير WCAG 2.2",
                "",
                "| المعيار | الاسم بالعربية | المستوى | الحالة المرصودة | طريقة الفحص |",
                "|---|---|---|---|---|",
            ]
        )

        for crit in report.wcag_criteria:
            crit_name = crit.criterion_name_ar.replace("|", "-")
            status_map = {
                "confirmed_failure": "❌ حاجز مؤكد",
                "potential_issue": "⚠️ ملاحظة محتملة",
                "passed_specific_check": "✅ اجتاز الفحص المحدد",
                "manual_review_required": "🔍 يتطلب مراجعة بشرية",
                "not_applicable": "➖ غير منطبق",
                "not_assessed": "⚪ لم يقيم",
            }
            lines.append(
                f"| **{crit.criterion_id}** | {crit_name} | `{crit.conformance_level}` | {status_map.get(crit.status, crit.status)} | `{crit.test_method}` |"
            )

        lines.extend(
            [
                "",
                "---",
                "",
                "## 15. المشكلات المؤكدة (Confirmed Failures)",
                "",
            ]
        )

        if not confirmed_findings:
            lines.append("لم يتم رصد أي حواجز نفاذ حرجة مؤكدة في العناصر المفحوصة آلياً.")
        else:
            for f in confirmed_findings:
                lines.append(f"### 🔴 {f.title_ar}")
                lines.append(f"- **المعيار المرتبط:** `{', '.join(f.wcag_criteria)}`")
                lines.append(f"- **مستوى الخطورة:** `{f.severity.upper()}` | **العنصر:** `{f.component_reference}`")
                lines.append(f"- **الوصف الفني:** {f.description_ar}")
                lines.append(f"- **الأثر على المستخدم:** {f.user_impact_ar}")
                lines.append(f"- **الإصلاح المقترح:** {f.recommended_fix_ar}")
                lines.append(f"- **الأدلة المسجلة:** `{', '.join(f.evidence_ids[:3])}`")
                lines.append("")

        lines.extend(
            [
                "---",
                "",
                "## 16. المشكلات المحتملة (Potential Issues)",
                "",
            ]
        )

        if not potential_findings:
            lines.append("لا توجد ملاحظات استرشادية إضافية.")
        else:
            for f in potential_findings[:5]:
                lines.append(f"#### 🟡 {f.title_ar}")
                lines.append(f"- **الوصف:** {f.description_ar}")
                lines.append(f"- **الإصلاح المقترح:** {f.recommended_fix_ar}")
                lines.append("")

        lines.extend(
            [
                "---",
                "",
                "## 17. الاختبارات البشرية المطلوبة (Manual Review Tasks)",
                "",
                "تتطلب الجوانب التالية تدقيقاً بشرياً لضمان تجربة نفاذ حقيقية وكاملة:",
                "",
            ]
        )

        for task in report.manual_review_tasks:
            lines.append(f"### 📋 {task.review_question_ar}")
            lines.append(f"- **معيار النفاذ:** `{task.wcag_criterion}` | **العنصر:** `{task.component_reference}`")
            lines.append(f"- **لماذا يتعذر الحسم الآلي؟** {task.why_automation_is_insufficient_ar}")
            lines.append("- **خطوات التحقق اليدوي:**")
            for step in task.manual_steps_ar:
                lines.append(f"  1. {step}")
            lines.append(f"- **السلوك المأمول:** {task.expected_accessible_behavior_ar}")
            lines.append("")

        lines.extend(
            [
                "---",
                "",
                "## 18. تقييم إمكانية الوصول بالأبعاد الموزونة",
                "",
                "| البعد التقييمي | الوزن | الدرجة المرصودة | الوصف |",
                "|---|---|---|---|",
                f"| **البنية الدلالية والأسماء المتاحة** | 20% | **{scores.semantics_names_score} / 100** | اكتمال المعالم والعناوين وأسماء الأزرار |",
                f"| **لوحة المفاتيح وإدارة التركيز** | 20% | **{scores.keyboard_focus_score} / 100** | وضوح مؤشر التركيز وغياب فخاخ التنقل |",
                f"| **التباين البصري والتجاوب** | 20% | **{scores.visual_contrast_score} / 100** | مقروئية النصوص وإعادة التدفق عند 320px |",
                f"| **النماذج والتفاعل الميسر** | 15% | **{scores.forms_interaction_score} / 100** | تسميات الحقول وارتباط رسائل الخطأ |",
                f"| **بنية التنقل وروابط التجاوز** | 15% | **{scores.navigation_structure_score} / 100** | روابط التجاوز السريع ومقاصد الروابط |",
                f"| **اللغة والوسائط والتجربة الشاملة** | 10% | **{scores.language_media_score} / 100** | إعلان سمة lang وترجمة مقاطع الفيديو |",
                f"| **التقييم العام المركب** | **100%** | **{scores.overall_score} / 100** | **{scores.score_label_ar}** |",
                "",
                "---",
                "",
                "## 19. التوصيات والإصلاحات ذات الأولوية (Remediation Roadmap)",
                "",
            ]
        )

        for rec in report.recommendations:
            lines.append(f"### [{rec.priority}] {rec.title_ar}")
            lines.append(f"- **المعايير المعالجة:** `{', '.join(rec.wcag_criteria)}`")
            lines.append(f"- **الحاجز المرصود:** {rec.observed_barrier_ar}")
            lines.append(f"- **خطوات المعالجة:** {rec.recommended_remediation_ar}")
            if rec.code_snippet:
                lines.append("```html")
                lines.append(rec.code_snippet)
                lines.append("```")
            lines.append(f"- **التوجيه الهندسي:** {rec.implementation_guidance_ar}")
            lines.append("")

        lines.extend(
            [
                "---",
                "",
                "## 20. حدود التقييم والملاحظات الختامية",
                "",
                "1. **طبيعة الفحص السلبي:** التدقيق يقتصر على الكود الظاهر والأدلة المتاحة دون تنفيذ محاكاة تفاعلية معقدة في المواقع الحية العامة لحماية استقرار الخوادم.",
                "2. **استقلالية الفحص الآلي عن قارئات الشاشة:** الفحص البرمجي يتحقق من توافق الشجرة الدلالية مع المعايير القياسية، لكنه لا يغني عن اختبار المستخدمين من ذوي الإعاقة بواسطة قارئات شاشة حقيقية (مثل NVDA أو VoiceOver).",
                "3. **تغطية العينة:** النتائج تنطبق على العينة الممثلة المختارة ولا تفترض سلامة باقي صفحات الموقع غير المفحوصة.",
                "",
                "**تم التوليد والاعتماد بواسطة محرك Site DNA Phase 10 — أساس للذكاء الاصطناعي.**",
            ]
        )

        return "\n".join(lines)
