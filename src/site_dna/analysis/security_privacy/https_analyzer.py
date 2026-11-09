"""HTTPS and Transport Security Analyzer for Site DNA Phase 09."""

import re
from typing import Optional

from site_dna.schemas.security_privacy import (
    HTTPSAssessment,
    SecurityPageRecord,
    TransportSecurityStatus,
)


class HTTPSAnalyzer:
    """Evaluates HTTPS adoption, HSTS headers, and transport security postures."""

    def analyze(self, page_records: list[SecurityPageRecord]) -> HTTPSAssessment:
        """Evaluate transport security based on recorded page records."""
        if not page_records:
            return HTTPSAssessment(
                status="transport_not_assessed",
                status_ar="لم يتم تقييم بروتوكول النقل",
                is_https=False,
                final_scheme="unknown",
                notes="No pages were available to assess transport security.",
                notes_ar="لم تتوفر صفحات لتقييم أمان النقل.",
            )

        primary_page = page_records[0]
        scheme = primary_page.scheme.lower()
        is_https = scheme == "https"

        # Check HSTS across inspected pages
        hsts_present = False
        hsts_val: Optional[str] = None
        hsts_max_age: Optional[int] = None
        hsts_preload = False
        hsts_include_sub = False
        evidence_ids: list[str] = []

        for idx, page in enumerate(page_records, start=1):
            headers = page.headers
            hsts_candidate = headers.get("strict-transport-security")
            if hsts_candidate:
                hsts_present = True
                hsts_val = hsts_candidate
                evidence_ids.append(f"ev-hsts-p{idx}")

                # Parse max-age
                ma_match = re.search(r"max-age=(\d+)", hsts_candidate, re.IGNORECASE)
                if ma_match:
                    try:
                        hsts_max_age = int(ma_match.group(1))
                    except ValueError:
                        pass

                if "preload" in hsts_candidate.lower():
                    hsts_preload = True
                if "includesubdomains" in hsts_candidate.lower():
                    hsts_include_sub = True
                break

        # Check redirect or scheme status
        status: TransportSecurityStatus = "https_observed" if is_https else "http_only_observed"
        status_ar = "بروتوكول HTTPS مفعل ومرصود" if is_https else "بروتوكول HTTP غير مشفر"

        if not is_https and any(p.scheme.lower() == "https" for p in page_records):
            status = "redirect_to_https_observed"
            status_ar = "تم رصد إعادة توجيه إلى HTTPS"

        mixed_scheme = any(p.scheme.lower() != scheme for p in page_records)

        notes = f"Primary page operates on {scheme.upper()}. " + (
            f"HSTS configured with max-age={hsts_max_age}." if hsts_present else "HSTS header is absent."
        )
        notes_ar = f"الصفحة الرئيسية تعمل عبر بروتوكول {scheme.upper()}. " + (
            f"ترويسة HSTS مفعلة بفترة max-age={hsts_max_age}." if hsts_present else "ترويسة HSTS غير مفعلة على الموقع."
        )

        return HTTPSAssessment(
            status=status,
            status_ar=status_ar,
            is_https=is_https,
            final_scheme=scheme,
            hsts_present=hsts_present,
            hsts_header_value=hsts_val,
            hsts_preload=hsts_preload,
            hsts_include_subdomains=hsts_include_sub,
            hsts_max_age=hsts_max_age,
            http_to_https_redirect_verified=is_https,
            mixed_scheme_observed=mixed_scheme,
            evidence_ids=evidence_ids,
            notes=notes,
            notes_ar=notes_ar,
        )
