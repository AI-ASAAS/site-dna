"""Browser Isolation and Context Control Analyzer for Site DNA Phase 09."""

from site_dna.schemas.security_privacy import (
    BrowserIsolationAssessment,
    SecurityPageRecord,
)


class BrowserIsolationAnalyzer:
    """Evaluates cross-origin isolation, referrer handling, and framing controls."""

    def analyze(self, page_records: list[SecurityPageRecord]) -> BrowserIsolationAssessment:
        """Inspect headers relevant to browser sandbox isolation."""
        if not page_records:
            return BrowserIsolationAssessment(
                notes="No pages available for browser isolation audit.",
                notes_ar="لا تتوفر صفحات لتقييم عزل بيئة المتصفح.",
            )

        # Aggregate headers from primary pages
        headers: dict[str, str] = {}
        for p in page_records:
            for k, v in p.headers.items():
                if k.lower() not in headers:
                    headers[k.lower()] = v

        coop = headers.get("cross-origin-opener-policy")
        coep = headers.get("cross-origin-embedder-policy")
        corp = headers.get("cross-origin-resource-policy")
        perm = headers.get("permissions-policy") or headers.get("feature-policy")
        ref = headers.get("referrer-policy")

        # Check framing protection
        csp = headers.get("content-security-policy", "").lower()
        has_frame_ancestors = "frame-ancestors" in csp
        xfo = headers.get("x-frame-options", "").upper()
        has_xfo = bool(xfo and ("DENY" in xfo or "SAMEORIGIN" in xfo))

        if has_frame_ancestors and has_xfo:
            framing_status = "both"
            framing_status_ar = "محمي بواسطة CSP frame-ancestors و X-Frame-Options معاً"
        elif has_frame_ancestors:
            framing_status = "protected_csp"
            framing_status_ar = "محمي بواسطة CSP frame-ancestors"
        elif has_xfo:
            framing_status = "protected_xfo"
            framing_status_ar = "محمي بواسطة X-Frame-Options"
        else:
            framing_status = "none"
            framing_status_ar = "غير محمي من التضمين (عرضة لاختطاف النقر المحتمل)"

        is_safe_ref = False
        if ref:
            r_lower = ref.lower()
            if any(s in r_lower for s in ("strict-origin", "no-referrer", "same-origin")):
                is_safe_ref = True

        evidence_ids: list[str] = []
        if coop:
            evidence_ids.append("ev-iso-coop")
        if perm:
            evidence_ids.append("ev-iso-perm")
        if ref:
            evidence_ids.append("ev-iso-ref")

        notes = (
            f"Framing Protection: {framing_status}. "
            f"Referrer-Policy: {'Safe' if is_safe_ref else (ref or 'Missing')}. "
            f"Cross-Origin Isolation: {'Enabled' if (coop and coep) else 'Standard'}."
        )
        notes_ar = (
            f"حماية التضمين (Anti-Clickjacking): {framing_status_ar}. "
            f"سياسة الإحالة: {'آمنة ومقيدة' if is_safe_ref else (ref or 'غير محددة')}. "
            f"عزل النوافذ المشتركة (COOP/COEP): {'مفعل' if (coop and coep) else 'قياسي'}."
        )

        return BrowserIsolationAssessment(
            has_coop=bool(coop),
            coop_value=coop,
            has_coep=bool(coep),
            coep_value=coep,
            has_corp=bool(corp),
            corp_value=corp,
            has_permissions_policy=bool(perm),
            permissions_policy_value=perm,
            has_referrer_policy=bool(ref),
            referrer_policy_value=ref,
            is_safe_referrer=is_safe_ref,
            framing_protection_status=framing_status,  # type: ignore
            framing_protection_status_ar=framing_status_ar,
            evidence_ids=evidence_ids,
            notes=notes,
            notes_ar=notes_ar,
        )
