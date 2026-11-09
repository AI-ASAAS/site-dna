"""Consent Interface and Cookie Banner Observations for Site DNA Phase 09."""

from typing import Any, Optional

from site_dna.schemas.security_privacy import (
    ConsentObservation,
    SecurityPageRecord,
)


class ConsentObservationsAnalyzer:
    """Detects visible consent banners and cookie dialogs without intrusive interaction."""

    def analyze(
        self,
        page_records: list[SecurityPageRecord],
        crawl_dataset: Optional[dict[str, Any]] = None,
    ) -> ConsentObservation:
        """Scan DOM and text for consent banner indicators."""
        if not page_records:
            return ConsentObservation(
                verification_mode="not_assessed",
                notes="No pages available to assess consent interface.",
                notes_ar="لا تتوفر صفحات لفحص واجهات الموافقة.",
            )

        banner_detected = False
        has_accept = False
        has_reject = False
        has_link = False
        summary = None
        summary_ar = None
        evidence_ids: list[str] = []

        p_data = (crawl_dataset or {}).get("pages", [])
        for idx, p in enumerate(p_data, start=1):
            html = (p.get("raw_html", "") or p.get("html", "") or "").lower()
            text = (p.get("text", "") or "").lower()

            # Check DOM signatures
            is_banner = bool(
                "cookie-banner" in html
                or "cookie-consent" in html
                or "onetrust" in html
                or "cookiebot" in html
                or "complianz" in html
                or "ملفات تعريف الارتباط" in text
            )

            if is_banner:
                banner_detected = True
                evidence_ids.append(f"ev-consent-dom-p{idx}")

                if any(w in text or w in html for w in ("accept", "agree", "allow", "موافق", "قبول الكل")):
                    has_accept = True
                if any(w in text or w in html for w in ("reject", "decline", "customize", "رفض", "إعدادات", "تفضيلات")):
                    has_reject = True
                if "cookie" in html and ("policy" in html or "سياسة" in text):
                    has_link = True

                summary = "Cookie consent management interface detected in DOM."
                summary_ar = "تم رصد واجهة إدارة موافقة ملفات تعريف الارتباط في هيكلية الصفحة (DOM)."
                break

        mode = "observed_in_dom" if banner_detected else "not_found_in_sample"

        notes = (
            f"Consent Banner: {'Detected' if banner_detected else 'Not found in sample'}. "
            f"Accept control: {'Yes' if has_accept else 'No'}, "
            f"Reject/Customize control: {'Yes' if has_reject else 'No'}."
        )
        notes_ar = (
            f"لافتة إدارة الموافقة: {'مرصودة' if banner_detected else 'غير موجودة ضمن العينة المفحوصة'}. "
            f"زر القبول: {'متوفر' if has_accept else 'غير مرصود'}، "
            f"زر الرفض أو التخصيص: {'متوفر' if has_reject else 'غير مرصود'}."
        )

        return ConsentObservation(
            consent_banner_detected=banner_detected,
            has_accept_button=has_accept,
            has_reject_or_customize=has_reject,
            has_link_to_cookie_policy=has_link,
            banner_text_summary=summary,
            banner_text_summary_ar=summary_ar,
            verification_mode=mode,  # type: ignore
            evidence_ids=evidence_ids,
            notes=notes,
            notes_ar=notes_ar,
        )
