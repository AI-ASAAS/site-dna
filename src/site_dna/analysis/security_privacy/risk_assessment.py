"""Risk Classification and Finding Synthesis for Site DNA Phase 09."""

import uuid

from site_dna.schemas.security_privacy import (
    BrowserIsolationAssessment,
    CookieSecurityAssessment,
    CSPAssessment,
    HTTPSAssessment,
    MixedContentAssessment,
    PrivacySignalAssessment,
    SecurityFinding,
    SecurityHeaderAssessment,
    SecurityPageRecord,
)


class RiskAssessmentEngine:
    """Classifies observable configurations into structured, evidence-backed security findings."""

    def synthesize_findings(
        self,
        page_records: list[SecurityPageRecord],
        https_assessment: HTTPSAssessment,
        headers_assessment: SecurityHeaderAssessment,
        csp_assessment: CSPAssessment,
        cookie_assessment: CookieSecurityAssessment,
        mixed_content_assessment: MixedContentAssessment,
        browser_isolation_assessment: BrowserIsolationAssessment,
        privacy_signal_assessment: PrivacySignalAssessment,
    ) -> list[SecurityFinding]:
        """Generate normalized findings across all assessed security domains."""
        findings: list[SecurityFinding] = []
        primary_page = page_records[0].page_url if page_records else "https://target"

        # 1. Transport findings
        if not https_assessment.is_https:
            findings.append(
                SecurityFinding(
                    finding_id=f"fnd-{uuid.uuid4().hex[:8]}",
                    title="Website Operating Over Unencrypted HTTP",
                    title_ar="الموقع يعمل عبر بروتوكول HTTP غير المشفر",
                    category="https_transport",
                    description="All user traffic and communications are transmitted in cleartext without TLS encryption.",
                    description_ar="يتم نقل حركة مرور المستخدمين والبيانات بنص صريح دون تشفير، مما يعرضها للاعتراض والتنصت.",
                    source_page=primary_page,
                    evidence_ids=https_assessment.evidence_ids or ["ev-transport-http"],
                    observation_type="observed",
                    verification_state="confirmed_configuration_issue",
                    severity="high",
                    confidence_category="observed",
                    potential_impact="Data interception and modification by network adversaries (man-in-the-middle).",
                    potential_impact_ar="اعتراض البيانات والتعديل عليها عبر شبكات الاتصال غير الموثوقة.",
                    recommended_action="Deploy an SSL/TLS certificate and enforce permanent 301 redirection to HTTPS.",
                    recommended_action_ar="تثبيت شهادة SSL/TLS وفرض إعادة توجيه دائمة (301) لكافة المسارات إلى HTTPS.",
                    limitations="Based on inspected public URL response.",
                    limitations_ar="بناءً على فحص الرد المباشر للرابط العام.",
                )
            )
        elif not https_assessment.hsts_present:
            findings.append(
                SecurityFinding(
                    finding_id=f"fnd-{uuid.uuid4().hex[:8]}",
                    title="HTTP Strict Transport Security (HSTS) Header Absent",
                    title_ar="غياب ترويسة HSTS لإلزام التشفير الصارم",
                    category="https_transport",
                    description="The server does not instruct browsers to exclusively use HTTPS for future requests.",
                    description_ar="الخادم لا يُلزم المتصفحات بالاتصال عبر HTTPS حصراً، مما يتيح محاولات الهبوط بالتشفير.",
                    source_page=primary_page,
                    evidence_ids=["ev-hsts-missing"],
                    observation_type="observed",
                    verification_state="confirmed_configuration_issue",
                    severity="medium",
                    confidence_category="observed",
                    potential_impact="Initial requests remain vulnerable to SSL stripping attacks before redirect.",
                    potential_impact_ar="الطلب الأولي قد يكون عرضة لهجمات تجريد التشفير (SSL Stripping).",
                    recommended_action="Enable Strict-Transport-Security with a minimum max-age of 31536000 and includeSubDomains.",
                    recommended_action_ar="تفعيل ترويسة Strict-Transport-Security بفترة لا تقل عن سنة مع شمول النطاقات الفرعية.",
                    limitations="HSTS should be tested carefully in staging prior to production deployment.",
                    limitations_ar="يجب اختبار تفعيل HSTS على بيئة تجريبية قبل النطاق الإنتاجي الكامل.",
                )
            )

        # 2. Security Headers findings
        for hdr in headers_assessment.header_records:
            if not hdr.is_present and hdr.header_name != "strict-transport-security":
                severity = (
                    "medium" if hdr.header_name in ("content-security-policy", "x-content-type-options") else "low"
                )
                findings.append(
                    SecurityFinding(
                        finding_id=f"fnd-{uuid.uuid4().hex[:8]}",
                        title=f"Missing Security Header: {hdr.header_name}",
                        title_ar=f"غياب ترويسة الأمان: {hdr.header_name}",
                        category="security_headers",
                        description=f"The defensive response header '{hdr.header_name}' was not detected in HTTP responses.",
                        description_ar=f"لم يتم رصد ترويسة الحماية '{hdr.header_name}' في ردود الخادم المفحوصة.",
                        source_page=primary_page,
                        evidence_ids=[f"ev-missing-hdr-{hdr.header_name}"],
                        observation_type="observed",
                        verification_state="confirmed_configuration_issue",
                        severity=severity,  # type: ignore
                        confidence_category="observed",
                        potential_impact=hdr.potential_risk or "Reduces client-side defense-in-depth posture.",
                        potential_impact_ar=hdr.potential_risk_ar
                        or "يقلل من مستويات الحماية الدفاعية التراكمية في المتصفح.",
                        recommended_action=hdr.remediation_recommendation or f"Configure {hdr.header_name} header.",
                        recommended_action_ar=hdr.remediation_recommendation_ar
                        or f"ضبط ترويسة {hdr.header_name} في الخادم.",
                        limitations="Applicability depends on the functional architecture of the application.",
                        limitations_ar="مدى الحاجة للترويسة يعتمد على الهيكلية الوظيفية للموقع.",
                    )
                )

        # 3. CSP specific weaknesses
        if csp_assessment.is_enforced:
            if csp_assessment.allows_unsafe_inline:
                findings.append(
                    SecurityFinding(
                        finding_id=f"fnd-{uuid.uuid4().hex[:8]}",
                        title="Content Security Policy Allows 'unsafe-inline' Scripts",
                        title_ar="سياسة CSP تسمح بالسكربتات المضمنة غير الآمنة ('unsafe-inline')",
                        category="csp",
                        description="CSP script-src contains 'unsafe-inline', significantly reducing defense against cross-site scripting.",
                        description_ar="تحتوي سياسة CSP على تعليمة 'unsafe-inline' مما يقلل فاعليتها في منع هجمات XSS.",
                        source_page=primary_page,
                        evidence_ids=csp_assessment.evidence_ids,
                        observation_type="observed",
                        verification_state="confirmed_configuration_issue",
                        severity="medium",
                        confidence_category="observed",
                        potential_impact="Injected inline script tags or event handlers would not be blocked by CSP.",
                        potential_impact_ar="لن يتمكن المتصفح من حجب نصوص السكربت المحقونة مضمنة في الصفحة.",
                        recommended_action="Migrate to cryptographic nonces or hashes for required inline scripts.",
                        recommended_action_ar="الاعتماد على التجزئة الرقمية (Hashes) أو الأرقام العشوائية (Nonces) للسكربتات المضمنة.",
                        limitations="Refactoring inline scripts requires development and regression testing.",
                        limitations_ar="إزالة السكربتات المضمنة تتطلب تعديلات برمجية واختبارات شاملة.",
                    )
                )
            if csp_assessment.allows_unsafe_eval:
                findings.append(
                    SecurityFinding(
                        finding_id=f"fnd-{uuid.uuid4().hex[:8]}",
                        title="Content Security Policy Allows Dynamic Code Execution ('unsafe-eval')",
                        title_ar="سياسة CSP تسمح بالتنفيذ الديناميكي للكود ('unsafe-eval')",
                        category="csp",
                        description="CSP allows string-to-code execution functions like eval(), setTimeout, and Function.",
                        description_ar="تتيح سياسة CSP تنفيذ النصوص البرمجية ديناميكياً مما يزيد من مخاطر استغلال الحقن.",
                        source_page=primary_page,
                        evidence_ids=csp_assessment.evidence_ids,
                        observation_type="observed",
                        verification_state="confirmed_configuration_issue",
                        severity="low",
                        confidence_category="observed",
                        potential_impact="Permits evaluation of arbitrary strings if user input reaches dynamic evaluation sinks.",
                        potential_impact_ar="يسمح بتنفيذ نصوص ديناميكية في حال وصول مدخلات المستخدم لدوال التقييم.",
                        recommended_action="Refactor application logic to eliminate eval() and remove 'unsafe-eval' from CSP.",
                        recommended_action_ar="إعادة بناء الكود للتخلي عن دوال eval واستبعادها من ترويسة CSP.",
                        limitations="Some client-side template engines require eval.",
                        limitations_ar="بعض محركات القوالب القديمة تتطلب eval لتعمل.",
                    )
                )

        # 4. Cookie findings
        if cookie_assessment.same_site_none_insecure_count > 0:
            findings.append(
                SecurityFinding(
                    finding_id=f"fnd-{uuid.uuid4().hex[:8]}",
                    title="Cookies with SameSite=None Missing Secure Flag",
                    title_ar="ملفات ارتباط تحمل SameSite=None تفتقر لسمة Secure",
                    category="cookie_security",
                    description=f"Identified {cookie_assessment.same_site_none_insecure_count} cookies configured with SameSite=None without Secure.",
                    description_ar=f"تم رصد {cookie_assessment.same_site_none_insecure_count} ملف ارتباط بخاصية SameSite=None دون تفعيل خاصية التشفير Secure.",
                    source_page=primary_page,
                    evidence_ids=cookie_assessment.evidence_ids,
                    observation_type="observed",
                    verification_state="confirmed_configuration_issue",
                    severity="high",
                    confidence_category="observed",
                    potential_impact="Modern browsers will reject these cookies or expose them to cross-site transmission risks.",
                    potential_impact_ar="المتصفحات الحديثة ترفض هذه الملفات أو تصبح عرضة لمخاطر النقل غير المشفر عبر المواقع.",
                    recommended_action="Always append the 'Secure' attribute whenever 'SameSite=None' is set.",
                    recommended_action_ar="إضافة سمة 'Secure' دائماً عند ضبط ملفات الارتباط بقيمة 'SameSite=None'.",
                    limitations="Assessed from publicly inspected Set-Cookie response attributes.",
                    limitations_ar="تم الفحص بناءً على سمات Set-Cookie المعلنة.",
                )
            )

        if cookie_assessment.apparent_session_cookies_missing_flags > 0:
            findings.append(
                SecurityFinding(
                    finding_id=f"fnd-{uuid.uuid4().hex[:8]}",
                    title="Potential Session Cookies Missing HttpOnly or Secure Flags",
                    title_ar="ملفات ارتباط يحتمل أنها تخص الجلسات تفتقر لسمات الحماية (HttpOnly / Secure)",
                    category="cookie_security",
                    description="Cookies whose names suggest session or authentication tokens lack expected defensive flags.",
                    description_ar="ملفات ارتباط تشير أسماؤها إلى إدارة الجلسات أو التوثيق تفتقر لسمة الحجب عن السكربتات أو التشفير.",
                    source_page=primary_page,
                    evidence_ids=cookie_assessment.evidence_ids,
                    observation_type="heuristic",
                    verification_state="potential_risk",
                    severity="medium",
                    confidence_category="inferred",
                    potential_impact="If these cookies hold session state, they could be accessed via client-side XSS or cleartext transit.",
                    potential_impact_ar="في حال كانت الملفات للجلسات، فإنها تصبح عرضة للقراءة بالسكربتات الخبيثة أو النقل غير المشفر.",
                    recommended_action="Review cookie issuance and enforce HttpOnly and Secure on all sensitive session tokens.",
                    recommended_action_ar="مراجعة ملفات الجلسات وضمان تفعيل خاصيتي HttpOnly و Secure لكافة الرموز السرية.",
                    limitations="Purpose inferred from standard cookie naming heuristics.",
                    limitations_ar="تم استنتاج الغرض من الأسماء القياسية الشائعة لملفات الارتباط.",
                )
            )

        # 5. Mixed Content findings
        if mixed_content_assessment.has_mixed_content:
            findings.append(
                SecurityFinding(
                    finding_id=f"fnd-{uuid.uuid4().hex[:8]}",
                    title="Insecure Mixed Content Resources Detected",
                    title_ar="رصد موارد غير مشفرة (محتوى مختلط) على صفحات HTTPS",
                    category="mixed_content",
                    description=f"Found {mixed_content_assessment.insecure_references_count} references to HTTP assets within HTTPS pages.",
                    description_ar=f"تم رصد {mixed_content_assessment.insecure_references_count} مورداً يتم استدعاؤه برابط HTTP غير مشفر ضمن صفحات مشفرة.",
                    source_page=primary_page,
                    evidence_ids=mixed_content_assessment.evidence_ids,
                    observation_type="observed",
                    verification_state="confirmed_configuration_issue",
                    severity="medium",
                    confidence_category="observed",
                    potential_impact="Insecure subresources can be blocked by browsers or intercepted by network attackers.",
                    potential_impact_ar="المتصفحات الحديثة تحجب الموارد غير المشفرة مما يسبب تعطل العرض أو تعرضه للتنصت.",
                    recommended_action="Update all internal and external asset URLs to relative paths or https://.",
                    recommended_action_ar="تحديث مسارات كافة الموارد والوسائط لتعمل عبر https:// حصراً.",
                    limitations="Based on inspected HTML source references.",
                    limitations_ar="بناءً على الروابط المرصودة في كود HTML.",
                )
            )

        # 6. Privacy findings
        if not privacy_signal_assessment.privacy_policy_found:
            findings.append(
                SecurityFinding(
                    finding_id=f"fnd-{uuid.uuid4().hex[:8]}",
                    title="No Accessible Privacy Policy Link Observed in Crawl Sample",
                    title_ar="لم يتم رصد رابط لسياسة الخصوصية ضمن عينة الصفحات المفحوصة",
                    category="privacy_policy",
                    description="No link to a public privacy statement or data policy was identified in the collected pages.",
                    description_ar="لم يُعثر على رابط واضح لسياسة الخصوصية أو معالجة البيانات ضمن الصفحات المفحوصة في العينة.",
                    source_page=primary_page,
                    evidence_ids=["ev-priv-missing"],
                    observation_type="observed",
                    verification_state="manual_review_required",
                    severity="low",
                    confidence_category="observed",
                    potential_impact="May affect user transparency and compliance with digital privacy standards.",
                    potential_impact_ar="قد يؤثر على شفافية المستخدمين والامتثال للمعايير التنظيمية للخصوصية الرقمية.",
                    recommended_action="Ensure a clear, accessible Privacy Policy link is available in website footers.",
                    recommended_action_ar="تضمين رابط واضح وسهل الوصول لسياسة الخصوصية في تذييل كافة صفحات الموقع.",
                    limitations="A privacy policy may exist on an uninspected page or external domain.",
                    limitations_ar="قد تتوفر السياسة في صفحة خارج نطاق عينة الزحف الحالية.",
                )
            )

        return findings
