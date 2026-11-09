"""HTTP Security Headers Analyzer for Site DNA Phase 09."""

from site_dna.schemas.security_privacy import (
    SecurityHeaderAssessment,
    SecurityHeaderRecord,
    SecurityPageRecord,
)

CORE_SECURITY_HEADERS = [
    {
        "name": "strict-transport-security",
        "title_ar": "ترويسة HSTS لفرض التشفير",
        "expected": "max-age=",
        "risk_ar": "غياب HSTS يجعل الاتصال الأولي عرضة لهجمات التجريد من التشفير (SSL Stripping).",
        "rec_ar": "إضافة ترويسة Strict-Transport-Security: max-age=31536000; includeSubDomains; preload",
    },
    {
        "name": "content-security-policy",
        "title_ar": "سياسة أمان المحتوى (CSP)",
        "expected": "default-src",
        "risk_ar": "غياب CSP يقلل من خطوط الدفاع ضد هجمات حقن السكربتات (XSS) وتضمين الوسائط الضارة.",
        "rec_ar": "تطبيق سياسة أمان محتوى صارمة تبدأ بتحديد default-src 'self' وتقييد المصادر الخارجية.",
    },
    {
        "name": "x-content-type-options",
        "title_ar": "منع تخمين نوع المحتوى (MIME Sniffing)",
        "expected": "nosniff",
        "risk_ar": "السماح للمتصفح بتخمين نوع الملفات قد يؤدي لتنفيذ نصوص غير موثوقة كملفات كود.",
        "rec_ar": "تعيين ترويسة X-Content-Type-Options: nosniff لجميع الردود.",
    },
    {
        "name": "x-frame-options",
        "title_ar": "الحماية من اختطاف النقر (Clickjacking)",
        "expected": "DENY|SAMEORIGIN",
        "risk_ar": "إمكانية تضمين صفحات الموقع داخل iframes خارجية لخداع المستخدمين بالنقر.",
        "rec_ar": "تعيين X-Frame-Options: SAMEORIGIN أو استخدام تعليمة frame-ancestors في CSP.",
    },
    {
        "name": "referrer-policy",
        "title_ar": "سياسة تسريب عنوان الإحالة (Referrer)",
        "expected": "strict-origin",
        "risk_ar": "تسريب مسارات الروابط الداخلية ومعرفات الجلسة المحتملة إلى مواقع خارجية.",
        "rec_ar": "تحديد Referrer-Policy: strict-origin-when-cross-origin لحماية خصوصية التنقل.",
    },
    {
        "name": "permissions-policy",
        "title_ar": "سياسة أذونات متصفح العميل (Permissions Policy)",
        "expected": "camera|geolocation|microphone",
        "risk_ar": "عدم تقييد وصول متصفح المستخدم إلى الكاميرا والميكروفون والموقع الجغرافي.",
        "rec_ar": "تفعيل Permissions-Policy لحجب الأجهزة الحساسة افتراضياً.",
    },
    {
        "name": "cross-origin-opener-policy",
        "title_ar": "سياسة عزل نوافذ التصفح (COOP)",
        "expected": "same-origin",
        "risk_ar": "مشاركة سياق تصفح موحد مع مواقع خارجية قد يعرض العمليات لهجمات القنوات الجانبية.",
        "rec_ar": "تعيين Cross-Origin-Opener-Policy: same-origin عند الحاجة لعزل بيئة التنفيذ.",
    },
    {
        "name": "cross-origin-resource-policy",
        "title_ar": "سياسة حماية الموارد عبر النطاقات (CORP)",
        "expected": "same-origin",
        "risk_ar": "إمكانية تحميل وقراءة موارد الموقع الحساسة من مواقع ومصادر خارجية غير مرخصة.",
        "rec_ar": "تعيين Cross-Origin-Resource-Policy: same-origin أو same-site لحماية الموارد الثابتة.",
    },
]


class SecurityHeadersAnalyzer:
    """Evaluates HTTP response security headers across collected page evidence."""

    def analyze(self, page_records: list[SecurityPageRecord]) -> SecurityHeaderAssessment:
        """Audit security headers on primary and secondary pages."""
        if not page_records:
            return SecurityHeaderAssessment(
                overall_headers_posture="not_assessed",
                overall_headers_posture_ar="لم يتم التقييم",
                notes="No pages available to inspect HTTP response headers.",
            )

        # Aggregate headers from primary page, falling back to any page
        headers: dict[str, str] = {}
        for p in page_records:
            for k, v in p.headers.items():
                if k.lower() not in headers:
                    headers[k.lower()] = v

        records: list[SecurityHeaderRecord] = []
        present_count = 0

        # Check each core header
        has_hsts = "strict-transport-security" in headers
        has_csp = "content-security-policy" in headers or "content-security-policy-report-only" in headers
        has_xcto = "x-content-type-options" in headers and "nosniff" in headers["x-content-type-options"].lower()
        has_ref = "referrer-policy" in headers
        has_perm = "permissions-policy" in headers or "feature-policy" in headers

        # Framing protection check: X-Frame-Options OR CSP frame-ancestors
        csp_val = headers.get("content-security-policy", "")
        has_csp_framing = "frame-ancestors" in csp_val.lower()
        has_xfo = "x-frame-options" in headers
        has_framing_prot = has_csp_framing or has_xfo

        for item in CORE_SECURITY_HEADERS:
            h_name = item["name"]
            val = headers.get(h_name)
            is_present = val is not None

            # Special case for framing: if X-Frame-Options is missing but CSP frame-ancestors is present, it's satisfied!
            if h_name == "x-frame-options" and not is_present and has_csp_framing:
                records.append(
                    SecurityHeaderRecord(
                        header_name=h_name,
                        is_present=False,
                        observed_value=None,
                        is_properly_configured=True,
                        status_ar="محمي عبر تعليمة CSP frame-ancestors",
                        potential_risk=None,
                        potential_risk_ar=None,
                        remediation_recommendation=None,
                        remediation_recommendation_ar=None,
                        evidence_ids=["ev-hdr-csp-framing"],
                    )
                )
                present_count += 1
                continue

            if is_present:
                present_count += 1
                is_proper = True
                if h_name == "x-content-type-options" and "nosniff" not in str(val).lower():
                    is_proper = False
                status_ar = "مفعل ومضبوط" if is_proper else "مفعل ولكن يتطلب تدقيق"
                records.append(
                    SecurityHeaderRecord(
                        header_name=h_name,
                        is_present=True,
                        observed_value=str(val)[:200],
                        is_properly_configured=is_proper,
                        status_ar=status_ar,
                        potential_risk=None if is_proper else "قيمة الترويسة قد لا تحقق الحماية الكاملة.",
                        potential_risk_ar=None if is_proper else "قيمة الترويسة قد لا تحقق الحماية الكاملة.",
                        remediation_recommendation=None,
                        remediation_recommendation_ar=None,
                        evidence_ids=[f"ev-hdr-{h_name}"],
                    )
                )
            else:
                records.append(
                    SecurityHeaderRecord(
                        header_name=h_name,
                        is_present=False,
                        observed_value=None,
                        is_properly_configured=False,
                        status_ar="غير مفعل",
                        potential_risk=f"Absence of {h_name} may weaken defense-in-depth.",
                        potential_risk_ar=item["risk_ar"],
                        remediation_recommendation=f"Deploy {h_name} header.",
                        remediation_recommendation_ar=item["rec_ar"],
                        evidence_ids=[],
                    )
                )

        total_checked = len(CORE_SECURITY_HEADERS)
        missing_count = total_checked - present_count

        posture = "strong" if present_count >= 5 else ("moderate" if present_count >= 3 else "weak")
        posture_ar = (
            "قوي ومتماسك" if posture == "strong" else ("متوسط" if posture == "moderate" else "ضعيف وبحاجة لتحسين")
        )

        notes = (
            f"Observed {present_count}/{total_checked} recommended security headers. "
            f"HSTS: {'Yes' if has_hsts else 'No'}, CSP: {'Yes' if has_csp else 'No'}, "
            f"Anti-Clickjacking: {'Protected' if has_framing_prot else 'Missing'}."
        )

        return SecurityHeaderAssessment(
            total_headers_checked=total_checked,
            present_headers_count=present_count,
            missing_headers_count=missing_count,
            header_records=records,
            has_hsts=has_hsts,
            has_csp=has_csp,
            has_x_content_type_options=has_xcto,
            has_referrer_policy=has_ref,
            has_permissions_policy=has_perm,
            has_framing_protection=has_framing_prot,
            overall_headers_posture=posture,
            overall_headers_posture_ar=posture_ar,
            notes=notes,
        )
