"""Digital Trust and Security Transparency Signals for Site DNA Phase 09."""

from typing import Any, Optional

from site_dna.schemas.security_privacy import (
    SecurityPageRecord,
    TrustSignalAssessment,
)


class TrustSignalsAnalyzer:
    """Audits public digital trust indicators and security transparency."""

    def analyze(
        self,
        page_records: list[SecurityPageRecord],
        crawl_dataset: Optional[dict[str, Any]] = None,
    ) -> TrustSignalAssessment:
        """Scan pages for security contact info, disclosure policies, and trust signals."""
        if not page_records:
            return TrustSignalAssessment(
                notes="No pages available to assess digital trust signals.",
                notes_ar="لا تتوفر صفحات لتقييم مؤشرات الثقة الرقمية.",
            )

        https_ind = page_records[0].scheme.lower() == "https"
        sec_contact = False
        sec_contact_url: Optional[str] = None
        vuln_disc = False
        claimed_seals: list[str] = []
        terms_found = False
        terms_url: Optional[str] = None
        evidence_ids: list[str] = []

        all_text = ""
        p_data = (crawl_dataset or {}).get("pages", [])
        for p in p_data:
            text = (p.get("text", "") or "").lower()
            all_text += " " + text
            url = p.get("url", "")

            if "/security" in url or "security.txt" in url:
                sec_contact = True
                sec_contact_url = url
                evidence_ids.append("ev-trust-sec-page")

            if "/terms" in url or "terms-of-service" in url or "الشروط والأحكام" in text:
                terms_found = True
                if not terms_url:
                    terms_url = url
                evidence_ids.append("ev-trust-terms")

            # Check for security disclosure / bug bounty wording
            if any(
                w in text
                for w in (
                    "vulnerability disclosure",
                    "report a vulnerability",
                    "security@",
                    "bug bounty",
                    "الإبلاغ عن ثغرة",
                )
            ):
                vuln_disc = True
                evidence_ids.append("ev-trust-disclosure")

            # Check for claimed certifications
            if "iso 27001" in text or "iso27001" in text:
                if "ISO 27001" not in claimed_seals:
                    claimed_seals.append("ISO 27001")
            if "soc 2" in text or "soc2" in text:
                if "SOC 2" not in claimed_seals:
                    claimed_seals.append("SOC 2")
            if "pci dss" in text or "pci-dss" in text:
                if "PCI DSS" not in claimed_seals:
                    claimed_seals.append("PCI DSS")

        notes = (
            f"HTTPS active: {'Yes' if https_ind else 'No'}. "
            f"Security Contact/Page: {'Observed' if sec_contact else 'Not found'}. "
            f"Vulnerability Disclosure Policy: {'Observed' if vuln_disc else 'Not observed'}. "
            f"Claimed Certifications: {', '.join(claimed_seals) if claimed_seals else 'None observed'}."
        )
        notes_ar = (
            f"اتصال مشفر HTTPS: {'مفعل' if https_ind else 'غير مفعل'}. "
            f"صفحة أو قناة التواصل الأمني: {'مرصودة' if sec_contact else 'غير متوفرة'}. "
            f"سياسة الإبلاغ عن الثغرات: {'مرصودة' if vuln_disc else 'غير معلنة'}. "
            f"الشهادات والمعايير المزعومة: {', '.join(claimed_seals) if claimed_seals else 'لم ترصد شهادات معلنة'}."
        )

        return TrustSignalAssessment(
            https_indicator=https_ind,
            security_contact_found=sec_contact,
            security_contact_url=sec_contact_url,
            vulnerability_disclosure_policy=vuln_disc,
            trust_seals_or_certifications_claimed=claimed_seals,
            independently_verified_certifications=[],  # Passive scanner cannot independently verify third-party certificates
            terms_of_service_found=terms_found,
            terms_of_service_url=terms_url,
            evidence_ids=evidence_ids,
            notes=notes,
            notes_ar=notes_ar,
        )
