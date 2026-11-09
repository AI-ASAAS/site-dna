"""Arabic Markdown and Structured Report Builder for Site DNA Phase 09."""

from site_dna.schemas.security_privacy import SecurityPrivacyReport


class SecurityReportBuilder:
    """Generates the comprehensive 16-section Arabic Markdown audit report."""

    def build_markdown_report(self, report: SecurityPrivacyReport) -> str:
        """Construct the complete 16-section Arabic audit report."""
        scores = report.scores
        stats = report.statistics
        headers_ast = report.security_headers_assessment
        https_ast = report.https_assessment
        cookie_ast = report.cookie_security_assessment
        csp_ast = report.csp_assessment
        mixed_ast = report.mixed_content_assessment
        iso_ast = report.browser_isolation_assessment
        res_ast = report.third_party_resource_assessment
        priv_ast = report.privacy_signal_assessment
        trust_ast = report.trust_signal_assessment

        score_display = (
            f"{scores.overall_score:.1f} / 100" if scores.overall_score is not None else "محجوب / قيد المراجعة"
        )

        md: list[str] = []

        # Header
        md.append(f"# تقرير تدقيق الأمان والخصوصية والثقة الرقمية — {report.site_origin}")
        md.append("")
        md.append("> **تنبيه وإخلاء مسؤولية أساسي:**")
        md.append(f"> {scores.disclaimer_ar}")
        md.append(
            "> *هذا التقييم هو فحص سلبي مبني على الأدلة العامة المرصودة، وليس اختبار اختراق (Penetration Test) أو شهادة أمنية معتمدة.*"
        )
        md.append("")
        md.append("---")
        md.append("")

        # 1. الملخص التنفيذي
        md.append("## 1. الملخص التنفيذي")
        md.append(
            f"تم إنجاز التدقيق الأمني السلبي لموقع **`{report.target_url}`** عبر تحليل الردود وترويسات الخادم والوسائط وملفات الارتباط ومؤشرات الخصوصية العامة."
        )
        md.append(f"- **مؤشر الوضع الأمني المرصود:** **{score_display}** ({scores.score_label_ar})")
        md.append(f"- **جاهزية النقل المشفر (HTTPS):** {https_ast.status_ar}")
        md.append(
            f"- **وضعية ترويسات الأمان:** {headers_ast.overall_headers_posture_ar} ({headers_ast.present_headers_count}/{headers_ast.total_headers_checked} ترويسة مرصودة)"
        )
        md.append(f"- **إجمالي المشكلات المرصودة:** {len(report.findings)} مشكلة وتكوين يتطلب مراجعة")
        md.append(f"- **التوصيات العلاجية ذات الأولوية:** {len(report.recommendations)} توصية دفاعية")
        md.append("")

        # 2. معلومات الفحص
        md.append("## 2. معلومات الفحص ونطاق التغطية")
        md.append(f"- **معرف الفحص الأمني:** `{report.security_run_id}`")
        md.append(f"- **معرف زحف الاستكشاف (Crawl ID):** `{report.crawl_run_id}`")
        md.append(f"- **معرف الالتقاط البصري (Visual ID):** `{report.visual_run_id or 'غير مرتبط'}`")
        md.append(f"- **تاريخ ووقت التحليل:** `{report.analysis_timestamp}`")
        md.append(f"- **عدد الصفحات المفحوصة:** {stats.pages_assessed} صفحة")
        md.append(f"- **نسبة تغطية الأدلة:** {scores.evidence_coverage_percentage:.1f}%")
        md.append(f"- **النموذج الذكي المعتمد:** `{report.model_name}`")
        md.append("")

        # 3. HTTPS وTLS
        md.append("## 3. فحص أمان النقل والتشفير (HTTPS & TLS)")
        md.append(f"- **الحالة:** {https_ast.status_ar}")
        md.append(f"- **البروتوكول النهائي:** `{https_ast.final_scheme.upper()}`")
        md.append(f"- **ترويسة HSTS لإلزام التشفير:** {'مفعلة' if https_ast.hsts_present else 'غير مفعلة'}")
        if https_ast.hsts_present:
            md.append(f"  - أقصى فترة احتفاظ (max-age): `{https_ast.hsts_max_age} ثانية`")
            md.append(
                f"  - شمول النطاقات الفرعية (includeSubDomains): {'نعم' if https_ast.hsts_include_subdomains else 'لا'}"
            )
            md.append(f"  - قائمة التثبيت المسبق (preload): {'نعم' if https_ast.hsts_preload else 'لا'}")
        md.append(f"- **ملاحظات النقل:** {https_ast.notes_ar}")
        md.append("")

        # 4. رؤوس الحماية
        md.append("## 4. تدقيق ترويسات أمان HTTP (Security Headers)")
        md.append("| الترويسة الأمنية | الحالة | القيمة المرصودة | الوضع والتوصية |")
        md.append("|---|---|---|---|")
        for h in headers_ast.header_records:
            val_snippet = f"`{h.observed_value[:35]}...`" if h.observed_value else "—"
            status_badge = "✅ مفعلة" if h.is_properly_configured else ("⚠️ تتطلب ضبط" if h.is_present else "❌ غائبة")
            md.append(f"| `{h.header_name}` | {status_badge} | {val_snippet} | {h.status_ar} |")
        md.append("")
        md.append(f"- **ملخص الترويسات:** {headers_ast.notes}")
        md.append("")

        # 5. سياسة أمان المحتوى
        md.append("## 5. تقييم سياسة أمان المحتوى (CSP)")
        md.append(
            f"- **حالة السياسة:** {'مفعلة بإلزام (Enforced)' if csp_ast.is_enforced else ('تقرير فقط (Report-Only)' if csp_ast.is_report_only else 'غير مطبقة')}"
        )
        md.append(f"- **مؤشر الدفاع المتعمق للسياسة:** `{csp_ast.defense_in_depth_score:.1f} / 100`")
        md.append(
            f"- **سماح بالسكربتات المضمنة ('unsafe-inline'):** {'نعم (يضعف الحماية)' if csp_ast.allows_unsafe_inline else 'لا (حماية جيدة)'}"
        )
        md.append(f"- **سماح بالتقييم الديناميكي ('unsafe-eval'):** {'نعم' if csp_ast.allows_unsafe_eval else 'لا'}")
        md.append(f"- **ملاحظات CSP:** {csp_ast.notes_ar}")
        md.append("")

        # 6. ملفات الارتباط
        md.append("## 6. فحص أمان وخصوصية ملفات الارتباط (Cookies)")
        md.append("> **تأكيد الخصوصية الصارم:** تم حجب وتعتيم كافة القيم السرية للرموز المعرفية (`[REDACTED]`).")
        md.append("")
        md.append(f"- **إجمالي ملفات الارتباط المرصودة:** {cookie_ast.total_cookies_observed}")
        md.append(f"- **الملفات المفعل عليها سمة Secure:** {cookie_ast.secure_cookies_count}")
        md.append(f"- **الملفات المحمية بـ HttpOnly ضد السكربتات:** {cookie_ast.http_only_cookies_count}")
        md.append(f"- **الملفات المضبوطة بـ SameSite:** {cookie_ast.same_site_configured_count}")
        if cookie_ast.cookie_records:
            md.append("")
            md.append("| اسم الملف | النطاق | Secure | HttpOnly | SameSite | الغرض المحتمل | ملاحظات المخاطر |")
            md.append("|---|---|---|---|---|---|---|")
            for c in cookie_ast.cookie_records[:8]:
                sec_icon = "✅" if c.is_secure else "❌"
                ho_icon = "✅" if c.is_http_only else "❌"
                risks = ", ".join(c.risk_flags_ar) if c.risk_flags_ar else "آمن ظاهرياً"
                md.append(
                    f"| `{c.name}` | `{c.domain or 'مضيف'}` | {sec_icon} | {ho_icon} | `{c.same_site}` | {c.apparent_purpose} | {risks} |"
                )
        md.append("")

        # 7. أمان المتصفح
        md.append("## 7. أمان وعزل المتصفح (Browser Isolation)")
        md.append(f"- **حماية اختطاف النقر (Framing Protection):** {iso_ast.framing_protection_status_ar}")
        md.append(f"- **سياسة الإحالة (Referrer-Policy):** `{iso_ast.referrer_policy_value or 'غير محددة'}`")
        md.append(f"- **سياسة عزل النوافذ (COOP):** `{iso_ast.coop_value or 'غير محددة'}`")
        md.append(
            f"- **سياسة أذونات الأجهزة (Permissions-Policy):** `{iso_ast.permissions_policy_value or 'غير محددة'}`"
        )
        md.append(f"- **ملاحظات العزل:** {iso_ast.notes_ar}")
        md.append("")

        # 8. المحتوى المختلط
        md.append("## 8. المحتوى المختلط (Mixed Content)")
        if mixed_ast.has_mixed_content:
            md.append(f"⚠️ **تم رصد {mixed_ast.insecure_references_count} مورد غير مشفر عبر HTTP داخل صفحات HTTPS:**")
            for m in mixed_ast.records[:5]:
                md.append(f"- نوع المورد: `{m.resource_type}` | الرابط: `{m.insecure_resource_url}`")
        else:
            md.append("✅ **لم يتم رصد أي استدعاءات لمحتوى مختلط غير مشفر (HTTP) ضمن صفحات HTTPS المفحوصة.**")
        md.append("")

        # 9. الموارد الخارجية
        md.append("## 9. جرد الموارد والنطاقات الخارجية (Third-Party Resources)")
        md.append(f"- **عدد النطاقات الخارجية الفريدة:** {res_ast.unique_third_party_origins}")
        md.append(f"- **أدوات التحليل والقياس (Analytics):** {'مرصودة' if res_ast.has_analytics else 'غير مرصودة'}")
        md.append(f"- **شبكات التتبع الإعلاني:** {'مرصودة' if res_ast.has_trackers else 'غير مرصودة'}")
        if res_ast.third_party_origins_list:
            md.append("")
            md.append("| النطاق الخارجي | التصنيف الوظيفي | مراجعة الخصوصية | الصفحات المرصودة |")
            md.append("|---|---|---|---|")
            for orig in res_ast.third_party_origins_list[:6]:
                rev_badge = "⚠️ مطلوبة" if orig.requires_privacy_review else "عادية"
                md.append(
                    f"| `{orig.origin}` | `{orig.resource_category}` | {rev_badge} | {len(orig.pages_observed)} صفحة |"
                )
        md.append("")

        # 10. الخصوصية والموافقات
        md.append("## 10. مؤشرات الخصوصية وواجهات الموافقة")
        md.append(
            f"- **رابط سياسة الخصوصية:** {'✅ متوفر' if priv_ast.privacy_policy_found else '❌ غير مرصود في العينة'}"
        )
        if priv_ast.privacy_policy_url:
            md.append(f"  - الرابط: `{priv_ast.privacy_policy_url}`")
        md.append(
            f"- **رابط سياسة ملفات تعريف الارتباط:** {'✅ متوفر' if priv_ast.cookie_policy_found else '❌ غير مرصود'}"
        )
        md.append(
            f"- **بيانات الاتصال بمسؤول الخصوصية:** {'✅ متوفرة' if priv_ast.privacy_contact_found else '❌ غير واضحة'}"
        )
        md.append(
            f"- **ذكر حقوق المستخدم القانونية:** {'✅ مرصودة' if priv_ast.user_rights_mentioned else '❌ غير مرصودة'}"
        )
        md.append(f"- **واجهة إدارة موافقة الكوكيز (Banner):** {report.consent_observation.notes_ar}")
        md.append("")

        # 11. مؤشرات الثقة
        md.append("## 11. مؤشرات الثقة والشفافية الرقمية")
        md.append(f"- **صفحة / قناة التواصل الأمني:** {'مرصودة' if trust_ast.security_contact_found else 'غير متوفرة'}")
        md.append(
            f"- **سياسة الإبلاغ عن الثغرات:** {'مرصودة' if trust_ast.vulnerability_disclosure_policy else 'غير معلنة'}"
        )
        md.append(f"- **الشروط والأحكام (Terms):** {'مرصودة' if trust_ast.terms_of_service_found else 'غير متوفرة'}")
        md.append(
            f"- **الشهادات الأمنية المزعومة:** {', '.join(trust_ast.trust_seals_or_certifications_claimed) if trust_ast.trust_seals_or_certifications_claimed else 'لا توجد مزاعم معلنة'}"
        )
        md.append("")

        # 12. تقييم المخاطر
        md.append("## 12. تقييم المخاطر وفق المنهجية الدفاعية")
        md.append("تم تصنيف النتائج استناداً إلى الأثر الدفاعي المحتمل ومستوى اليقين المرصود:")
        md.append(f"- **مشكلات عالية الأهمية (High):** {stats.findings_count_by_severity.get('high', 0)}")
        md.append(f"- **مشكلات متوسطة الأهمية (Medium):** {stats.findings_count_by_severity.get('medium', 0)}")
        md.append(f"- **مشكلات منخفضة الأهمية (Low):** {stats.findings_count_by_severity.get('low', 0)}")
        md.append(f"- **تنبيهات إعلامية (Informational):** {stats.findings_count_by_severity.get('informational', 0)}")
        md.append("")

        # 13. التقييم العام
        md.append("## 13. تفصيل مؤشر الوضع الأمني (Posture Scores)")
        md.append("| البُعد الأمني | الوزن النسبي | الدرجة المرصودة |")
        md.append("|---|---|---|")
        md.append(f"| أمان النقل وتشفير HTTPS | 20% | `{scores.https_transport_score or 0:.1f} / 100` |")
        md.append(f"| ترويسات أمان HTTP | 25% | `{scores.security_headers_score or 0:.1f} / 100` |")
        md.append(f"| أمان ملفات الارتباط (Cookies) | 15% | `{scores.cookie_security_score or 0:.1f} / 100` |")
        md.append(f"| أمان جانب العميل وعزل المتصفح | 15% | `{scores.client_side_resources_score or 0:.1f} / 100` |")
        md.append(f"| مؤشرات الخصوصية والموافقة | 15% | `{scores.privacy_consent_score or 0:.1f} / 100` |")
        md.append(f"| الثقة الرقمية والشفافية | 10% | `{scores.digital_trust_score or 0:.1f} / 100` |")
        md.append(f"| **المؤشر العام التراكمي** | **100%** | **`{scores.overall_score or 0:.1f} / 100`** |")
        md.append("")

        # 14. المشكلات المكتشفة
        md.append("## 14. المشكلات والملاحظات المكتشفة المدعومة بالأدلة")
        if report.findings:
            for idx, f in enumerate(report.findings, start=1):
                md.append(f"### {idx}. [{f.severity.upper()}] {f.title_ar}")
                md.append(f"- **التصنيف:** `{f.category}` | **حالة التحقق:** `{f.verification_state}`")
                md.append(f"- **الوصف:** {f.description_ar}")
                md.append(f"- **الأثر المحتمل:** {f.potential_impact_ar}")
                md.append(f"- **الإجراء الموصى به:** {f.recommended_action_ar}")
                md.append(f"- **معرفات الأدلة:** `{', '.join(f.evidence_ids)}`")
                md.append("")
        else:
            md.append("لم يتم رصد أي مشكلات أمنية ظاهرة ضمن نطاق الفحص.")
            md.append("")

        # 15. التوصيات
        md.append("## 15. التوصيات العلاجية ذات الأولوية (P1 / P2 / P3)")
        if report.recommendations:
            for idx, r in enumerate(report.recommendations, start=1):
                p_badge = (
                    "🔴 أولوية قصوى (P1)"
                    if r.priority == "p1"
                    else ("🟡 أولوية متوسطة (P2)" if r.priority == "p2" else "🟢 أولوية عادية (P3)")
                )
                md.append(f"### {idx}. {p_badge}: {r.title_ar}")
                md.append(
                    f"- **التصنيف:** {r.category_ar} | **الأثر التقديري:** `{r.estimated_impact}` | **الجهد التقديري:** `{r.estimated_effort}`"
                )
                md.append(f"- **المشكلة المرصودة:** {r.observed_issue_ar}")
                md.append(f"- **التعديل الموصى به:** `{r.recommended_configuration_change_ar}`")
                md.append(f"- **طريقة التحقق من الإصلاح:** {r.verification_method_ar}")
                md.append(f"- **الحدود والمحاذير:** {r.limitations_ar}")
                md.append("")
        md.append("")

        # 16. حدود الفحص
        md.append("## 16. حدود ونطاق الفحص الأمني السلبي")
        md.append(
            "1. **طبيعة الفحص السلبي (Passive Only):** تم تنفيذ هذا الفحص دون إرسال أي حمولات برمجية هجومية أو محاولات اختراق أو تجربة حقن ثغرات، ولا يمثل شهادة ضمان بخلو الموقع من الثغرات."
        )
        md.append(
            "2. **حدود العينة المفحوصة:** الفحص مقتصر على عينة الصفحات المرصودة في جولة الزحف الحالية؛ الصفحات أو اللوحات التي تتطلب تسجيل دخول لم يتم فحصها."
        )
        md.append(
            "3. **عدم إثبات قابلية الاستغلال:** غياب بعض ترويسات الأمان أو سمات ملفات الارتباط يمثل ضعفاً في خطوط الدفاع المتعمق ولا يثبت بالضرورة وجود ثغرة قابلة للاستغلال المباشر."
        )
        md.append(
            "4. **الامتثال القانوني:** مؤشرات الخصوصية تعبر عن الملاحظات التقنية الظاهرة ولا تعد استشارة قانونية أو شهادة امتثال لأنظمة حماية البيانات (مثل GDPR أو PDPL)."
        )
        md.append("")
        md.append("---")
        md.append("*تم توليد هذا التقرير آلياً بواسطة منظومة Site DNA (المرحلة 09) — شركة أساس للذكاء الاصطناعي.*")

        return "\n".join(md)
