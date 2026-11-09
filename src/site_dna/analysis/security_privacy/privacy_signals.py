"""Privacy Signals and Disclosures Analyzer for Site DNA Phase 09."""

from typing import Any, Optional

from site_dna.schemas.security_privacy import (
    PrivacySignalAssessment,
    SecurityPageRecord,
)


class PrivacySignalsAnalyzer:
    """Audits publicly observable privacy disclosures and policy links."""

    def analyze(
        self,
        page_records: list[SecurityPageRecord],
        crawl_dataset: Optional[dict[str, Any]] = None,
    ) -> PrivacySignalAssessment:
        """Scan page text and links for public privacy statements."""
        if not page_records:
            return PrivacySignalAssessment(
                notes="No pages available to assess privacy signals.",
                notes_ar="لا تتوفر صفحات لفحص مؤشرات الخصوصية.",
            )

        policy_found = False
        policy_url: Optional[str] = None
        cookie_found = False
        cookie_url: Optional[str] = None
        contact_found = False
        contact_method: Optional[str] = None
        retention_mentioned = False
        sharing_mentioned = False
        rights_mentioned = False
        dpo_mentioned = False
        evidence_ids: list[str] = []

        all_text = ""
        p_data = (crawl_dataset or {}).get("pages", [])
        for p in p_data:
            all_text += " " + (p.get("text", "") or "")
            html = (p.get("raw_html", "") or p.get("html", "") or "").lower()
            url = p.get("url", "")

            if "/privacy" in url or "privacy-policy" in url:
                policy_found = True
                policy_url = url
            if "/cookie" in url or "cookies-policy" in url:
                cookie_found = True
                cookie_url = url

            # Link checks in HTML
            if "سياسة الخصوصية" in html or "privacy policy" in html:
                policy_found = True
                if not policy_url:
                    policy_url = url

            if "سياسة ملفات تعريف الارتباط" in html or "cookie policy" in html:
                cookie_found = True
                if not cookie_url:
                    cookie_url = url

        # Scan text for specific disclosures
        text_lower = all_text.lower()
        if any(w in text_lower for w in ("privacy@", "dpo@", "data-protection@", "مسؤول حماية البيانات")):
            contact_found = True
            contact_method = "Dedicated privacy contact address observed in text"
            evidence_ids.append("ev-priv-contact")

        if any(w in text_lower for w in ("retention", "احتفاظ بالبيانات", "فترة الاحتفاظ", "delete your data")):
            retention_mentioned = True
            evidence_ids.append("ev-priv-retention")

        if any(w in text_lower for w in ("third party", "third-party", "مشاركة البيانات", "أطراف ثالثة")):
            sharing_mentioned = True
            evidence_ids.append("ev-priv-sharing")

        if any(w in text_lower for w in ("gdpr", "ccpa", "حق الوصول", "حق المسح", "حقوق المستخدم", "right to access")):
            rights_mentioned = True
            evidence_ids.append("ev-priv-rights")

        if any(w in text_lower for w in ("dpo", "data protection officer", "مسؤول حماية البيانات")):
            dpo_mentioned = True
            evidence_ids.append("ev-priv-dpo")

        if policy_found:
            evidence_ids.append("ev-priv-policy")

        notes = (
            f"Privacy Policy link: {'Observed' if policy_found else 'Not found in sample'}. "
            f"Cookie Policy: {'Observed' if cookie_found else 'Not found in sample'}. "
            f"User Rights Mentioned: {'Yes' if rights_mentioned else 'No'}."
        )
        notes_ar = (
            f"رابط سياسة الخصوصية: {'مرصود ومتاح' if policy_found else 'غير موجود ضمن العينة المفحوصة'}. "
            f"سياسة ملفات تعريف الارتباط: {'مرصودة' if cookie_found else 'غير موجودة ضمن العينة المفحوصة'}. "
            f"حقوق المستخدم القانونية: {'مذكورة في النصوص' if rights_mentioned else 'غير واضحة في العينة'}."
        )

        return PrivacySignalAssessment(
            privacy_policy_found=policy_found,
            privacy_policy_url=policy_url,
            cookie_policy_found=cookie_found,
            cookie_policy_url=cookie_url,
            privacy_contact_found=contact_found,
            privacy_contact_method=contact_method,
            data_retention_mentioned=retention_mentioned,
            third_party_sharing_mentioned=sharing_mentioned,
            user_rights_mentioned=rights_mentioned,
            dpo_or_officer_mentioned=dpo_mentioned,
            evidence_ids=evidence_ids,
            notes=notes,
            notes_ar=notes_ar,
        )
