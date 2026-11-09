"""Remediation Recommendation Engine for Site DNA Phase 09."""

import uuid

from site_dna.schemas.security_privacy import (
    SecurityFinding,
    SecurityRecommendation,
)


class SecurityRecommendationEngine:
    """Derives prioritized, actionable remediation recommendations from findings."""

    def derive_recommendations(self, findings: list[SecurityFinding]) -> list[SecurityRecommendation]:
        """Convert findings into prioritized defensive configuration steps."""
        recommendations: list[SecurityRecommendation] = []
        seen_topics: set[str] = set()

        for f in findings:
            topic = f.category
            rec_id = f"rec-{uuid.uuid4().hex[:8]}"

            if topic == "https_transport":
                if "HTTP" in f.title:
                    recommendations.append(
                        SecurityRecommendation(
                            recommendation_id=rec_id,
                            title="Migrate Web Traffic to Enforced HTTPS",
                            title_ar="ترحيل وإلزام حركة المرور لتعمل عبر بروتوكول HTTPS المشفر",
                            related_finding_ids=[f.finding_id],
                            category="https_transport",
                            category_ar="أمان النقل والتشفير",
                            affected_pages=[f.source_page],
                            observed_issue=f.description,
                            observed_issue_ar=f.description_ar,
                            evidence_ids=f.evidence_ids,
                            security_or_privacy_implication="Cleartext transmission allows eavesdropping and credential theft.",
                            security_or_privacy_implication_ar="نقل البيانات بنص صريح يعرضها للتنصت والسرقة في الشبكات العامة.",
                            recommended_configuration_change="Install a valid TLS certificate and configure server to return 301 redirects to HTTPS.",
                            recommended_configuration_change_ar="تثبيت شهادة TLS صالحة وضبط خادم الويب لإرجاع إعادة توجيه دائمة (301) إلى HTTPS.",
                            estimated_effort="medium",
                            estimated_impact="high",
                            priority="p1",
                            verification_method="curl -I http://yourdomain.com must return 301 Moved Permanently pointing to https://.",
                            verification_method_ar="فحص استجابة curl -I http://yourdomain.com والتأكد من إرجاع 301 إلى رابط https://.",
                            limitations="Ensure all internal links and assets support HTTPS before switching.",
                            limitations_ar="التأكد من دعم كافة الروابط الداخلية والوسائط لبروتوكول HTTPS قبل التفعيل.",
                        )
                    )
                elif "HSTS" in f.title and "hsts" not in seen_topics:
                    seen_topics.add("hsts")
                    recommendations.append(
                        SecurityRecommendation(
                            recommendation_id=rec_id,
                            title="Deploy HTTP Strict Transport Security (HSTS)",
                            title_ar="تفعيل ترويسة HSTS لإلزام التشفير الصارم وحظر التجريد",
                            related_finding_ids=[f.finding_id],
                            category="https_transport",
                            category_ar="أمان النقل والتشفير",
                            affected_pages=[f.source_page],
                            observed_issue=f.description,
                            observed_issue_ar=f.description_ar,
                            evidence_ids=f.evidence_ids,
                            security_or_privacy_implication="Protects against SSL stripping and man-in-the-middle attacks.",
                            security_or_privacy_implication_ar="يحمي من هجمات تجريد التشفير وهجمات الوسيط (MitM).",
                            recommended_configuration_change="Strict-Transport-Security: max-age=31536000; includeSubDomains; preload",
                            recommended_configuration_change_ar="تعيين Strict-Transport-Security: max-age=31536000; includeSubDomains; preload في ردود الخادم.",
                            estimated_effort="small",
                            estimated_impact="high",
                            priority="p2",
                            verification_method="Inspect response headers via curl -I https://yourdomain.com | grep -i strict-transport-security",
                            verification_method_ar="فحص ترويسات الرد عبر أداة curl والتأكد من ظهور Strict-Transport-Security.",
                            limitations="Verify that all subdomains support HTTPS before enabling includeSubDomains.",
                            limitations_ar="التأكد من أن جميع النطاقات الفرعية تدعم HTTPS قبل تفعيل includeSubDomains.",
                        )
                    )

            elif topic == "cookie_security":
                if "SameSite=None" in f.title and "cookie_samesite" not in seen_topics:
                    seen_topics.add("cookie_samesite")
                    recommendations.append(
                        SecurityRecommendation(
                            recommendation_id=rec_id,
                            title="Append Secure Flag to All SameSite=None Cookies",
                            title_ar="إضافة سمة Secure لكافة ملفات الارتباط ذات القيمة SameSite=None",
                            related_finding_ids=[f.finding_id],
                            category="cookie_security",
                            category_ar="أمان ملفات الارتباط (Cookies)",
                            affected_pages=[f.source_page],
                            observed_issue=f.description,
                            observed_issue_ar=f.description_ar,
                            evidence_ids=f.evidence_ids,
                            security_or_privacy_implication="Prevents cookie rejection in modern browsers and protects cross-site transmission.",
                            security_or_privacy_implication_ar="يمنع رفض المتصفحات لملفات الارتباط ويحمي نقلها عبر المواقع.",
                            recommended_configuration_change="Update cookie generation to: Set-Cookie: name=...; SameSite=None; Secure",
                            recommended_configuration_change_ar="تعديل دالة إنشاء ملف الارتباط لتشمل سمة Secure مع SameSite=None دائماً.",
                            estimated_effort="small",
                            estimated_impact="high",
                            priority="p1",
                            verification_method="Inspect Set-Cookie headers in browser DevTools Application > Cookies tab.",
                            verification_method_ar="فحص ترويسات Set-Cookie في أدوات مطوري المتصفح والتأكد من تفعيل Secure.",
                            limitations="Requires HTTPS for delivery.",
                            limitations_ar="يتطلب عمل الموقع عبر HTTPS ليتم قبول الملف.",
                        )
                    )
                elif "Session" in f.title and "cookie_session" not in seen_topics:
                    seen_topics.add("cookie_session")
                    recommendations.append(
                        SecurityRecommendation(
                            recommendation_id=rec_id,
                            title="Enforce HttpOnly and Secure on Sensitive Session Cookies",
                            title_ar="إلزام تفعيل خاصيتي HttpOnly و Secure على ملفات الجلسات والتوثيق",
                            related_finding_ids=[f.finding_id],
                            category="cookie_security",
                            category_ar="أمان ملفات الارتباط (Cookies)",
                            affected_pages=[f.source_page],
                            observed_issue=f.description,
                            observed_issue_ar=f.description_ar,
                            evidence_ids=f.evidence_ids,
                            security_or_privacy_implication="Prevents XSS-based session hijacking and network interception.",
                            security_or_privacy_implication_ar="يمنع سرقة جلسات المستخدمين عبر ثغرات XSS أو الاعتراض الشبكي.",
                            recommended_configuration_change="Set-Cookie: session_id=...; Secure; HttpOnly; SameSite=Lax; Path=/",
                            recommended_configuration_change_ar="ضبط ملفات الجلسات لتشمل HttpOnly و Secure و SameSite=Lax.",
                            estimated_effort="small",
                            estimated_impact="high",
                            priority="p2",
                            verification_method="Verify document.cookie in browser console does not expose session identifiers.",
                            verification_method_ar="التحقق من أن استدعاء document.cookie في المتصفح لا يعرض معرفات الجلسة الحساسة.",
                            limitations="JavaScript cannot read HttpOnly cookies by design.",
                            limitations_ar="السكربتات البرمجية لن تتمكن من قراءة ملف الارتباط بعد تفعيل HttpOnly.",
                        )
                    )

            elif topic == "csp" and "csp_policy" not in seen_topics:
                seen_topics.add("csp_policy")
                recommendations.append(
                    SecurityRecommendation(
                        recommendation_id=rec_id,
                        title="Strengthen Content Security Policy Directives",
                        title_ar="تعزيز وضبط سياسة أمان المحتوى (CSP) وتقييد المصادر الموثوقة",
                        related_finding_ids=[f.finding_id],
                        category="csp",
                        category_ar="سياسة أمان المحتوى (CSP)",
                        affected_pages=[f.source_page],
                        observed_issue=f.description,
                        observed_issue_ar=f.description_ar,
                        evidence_ids=f.evidence_ids,
                        security_or_privacy_implication="Limits execution surface for cross-site scripting and unauthorized resources.",
                        security_or_privacy_implication_ar="يقلل مساحة الهجوم لهجمات XSS وتحميل الموارد غير المصرح بها.",
                        recommended_configuration_change="Define default-src 'self'; script-src 'self' 'nonce-...'; object-src 'none';",
                        recommended_configuration_change_ar="تعريف سياسة تبدأ بـ default-src 'self' واستخدام nonces وتعيين object-src 'none'.",
                        estimated_effort="medium",
                        estimated_impact="medium",
                        priority="p2",
                        verification_method="Test initially in Content-Security-Policy-Report-Only mode and monitor violation reports.",
                        verification_method_ar="البدء بوضع التقرير فقط (Report-Only) ومراقبة التقارير قبل فرضه كسياسة إلزامية.",
                        limitations="Overly strict CSP can break dynamic UI components if not tested thoroughly.",
                        limitations_ar="السياسة الصارمة غير المختبرة قد تعطل عناصر تفاعلية في الواجهة.",
                    )
                )

            elif topic == "mixed_content" and "mixed_content" not in seen_topics:
                seen_topics.add("mixed_content")
                recommendations.append(
                    SecurityRecommendation(
                        recommendation_id=rec_id,
                        title="Eliminate Insecure Mixed Content Subresources",
                        title_ar="معالجة موارد المحتوى المختلط غير المشفرة وتحديثها لتعمل عبر HTTPS",
                        related_finding_ids=[f.finding_id],
                        category="mixed_content",
                        category_ar="المحتوى المختلط (Mixed Content)",
                        affected_pages=[f.source_page],
                        observed_issue=f.description,
                        observed_issue_ar=f.description_ar,
                        evidence_ids=f.evidence_ids,
                        security_or_privacy_implication="Prevents browser blocking of images, styles, or scripts on secure pages.",
                        security_or_privacy_implication_ar="يمنع حجب المتصفحات للصور والسكربتات غير المشفرة على الصفحات الآمنة.",
                        recommended_configuration_change="Update resource links in templates to https:// or relative paths.",
                        recommended_configuration_change_ar="تحديث روابط الموارد والوسائط في القوالب لتكون نسبية أو تبدأ بـ https://.",
                        estimated_effort="small",
                        estimated_impact="high",
                        priority="p1",
                        verification_method="Check browser console on HTTPS pages for mixed content warnings.",
                        verification_method_ar="فحص وحدة تحكم المتصفح (Console) والتأكد من خلوها من تنبيهات Mixed Content.",
                        limitations="External third-party providers must also support HTTPS.",
                        limitations_ar="المزودون الخارجيون للموارد يجب أن يدعموا بروتوكول HTTPS.",
                    )
                )

        # Fallback recommendations if none derived
        if not recommendations:
            recommendations.append(
                SecurityRecommendation(
                    recommendation_id=f"rec-{uuid.uuid4().hex[:8]}",
                    title="Regular Passive Security Configuration Audits",
                    title_ar="المراجعة الدورية المنتظمة لإعدادات الحماية وترويسات الخادم",
                    related_finding_ids=[],
                    category="general_security",
                    category_ar="الأمان العام",
                    affected_pages=["/"],
                    observed_issue="Continuous observation is recommended to catch configuration drift.",
                    observed_issue_ar="يوصى بالمتابعة الدورية لمنع تراخي الإعدادات الأمنية مع التحديثات المتتابعة.",
                    evidence_ids=["ev-audit-general"],
                    security_or_privacy_implication="Maintains robust defensive posture over time.",
                    security_or_privacy_implication_ar="الحفاظ على جاهزية خطوط الدفاع مع كل تحديث للموقع أو البنية التحتية.",
                    recommended_configuration_change="Integrate security header checks into continuous deployment pipelines.",
                    recommended_configuration_change_ar="دمج فحص ترويسات الأمان في خطوط النشر الآلي (CI/CD).",
                    estimated_effort="small",
                    estimated_impact="medium",
                    priority="p3",
                    verification_method="Automated pipeline regression testing.",
                    verification_method_ar="فحوصات التراجع الآلية في خطوط النشر.",
                    limitations="Complements but does not replace periodic authorized penetration testing.",
                    limitations_ar="مكمل للفحوصات الدورية المعتمدة ولا يغني عن اختبار الاختراق المصرح به.",
                )
            )

        return recommendations[:10]
