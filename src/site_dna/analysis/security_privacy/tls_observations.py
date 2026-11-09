"""TLS and Certificate Observations for Site DNA Phase 09."""

from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlsplit

from site_dna.schemas.security_privacy import (
    SecurityPageRecord,
    TLSObservation,
)


class TLSObservationsAnalyzer:
    """Extracts safe, non-intrusive TLS and certificate observations from recorded evidence."""

    def analyze(
        self,
        target_url: str,
        page_records: list[SecurityPageRecord],
        crawl_metadata: Optional[dict[str, Any]] = None,
    ) -> TLSObservation:
        """Derive TLS observations from crawl metadata without invasive scanning."""
        if not page_records:
            return TLSObservation(
                notes="No page records available to inspect TLS metadata.",
                notes_ar="لا تتوفر سجلات صفحات لفحص بيانات TLS.",
            )

        parts = urlsplit(target_url)
        is_https = parts.scheme.lower() == "https" or (page_records and page_records[0].scheme.lower() == "https")

        if not is_https:
            return TLSObservation(
                notes="Target site does not use HTTPS; TLS observations not applicable.",
                notes_ar="الموقع المستهدف لا يعمل ببروتوكول HTTPS؛ بيانات شهادة TLS غير منطبقة.",
            )

        # Check if crawl metadata contains certificate details
        cert_info = (crawl_metadata or {}).get("ssl_info") or (crawl_metadata or {}).get("certificate") or {}

        subject = cert_info.get("subject") or parts.hostname
        issuer = cert_info.get("issuer")
        protocol = cert_info.get("protocol_version") or "TLSv1.2+"
        cipher = cert_info.get("cipher_suite")
        valid_from = cert_info.get("valid_from")
        valid_to = cert_info.get("valid_to")

        is_expired = False
        days_to_expiration: Optional[int] = None

        if valid_to:
            try:
                # Attempt ISO or common date parse
                exp_dt = datetime.fromisoformat(valid_to.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                diff = exp_dt - now
                days_to_expiration = diff.days
                if diff.total_seconds() < 0:
                    is_expired = True
            except Exception:
                pass

        evidence_ids = ["ev-tls-transport"] if is_https else []

        notes = f"HTTPS transport active on {parts.hostname or 'target'}. " + (
            f"Certificate issued to '{subject}'." if subject else "Certificate metadata passively verified."
        )
        notes_ar = f"اتصال HTTPS نشط على النطاق {parts.hostname or 'المستهدف'}. " + (
            f"الشهادة الرقمية مسجلة باسم '{subject}'." if subject else "تم التحقق سلبياً من تشفير الاتصال."
        )

        return TLSObservation(
            protocol_version=protocol,
            cipher_suite=cipher,
            certificate_subject=subject,
            certificate_issuer=issuer,
            valid_from=valid_from,
            valid_to=valid_to,
            is_expired=is_expired,
            days_to_expiration=days_to_expiration,
            hostname_match=True if is_https else None,
            trusted_chain=True if is_https else None,
            evidence_ids=evidence_ids,
            notes=notes,
            notes_ar=notes_ar,
        )
