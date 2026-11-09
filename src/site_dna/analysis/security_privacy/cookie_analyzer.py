"""Cookie Security and Privacy Analyzer for Site DNA Phase 09."""

import re
from typing import Any, Optional

from site_dna.schemas.security_privacy import (
    CookieAttributeRecord,
    CookieSecurityAssessment,
    SecurityPageRecord,
)

# Common session identifier heuristics
SESSION_COOKIE_NAMES = {
    "session",
    "sessionid",
    "sess_id",
    "phpsessid",
    "jsessionid",
    "aspsessionid",
    "connect.sid",
    "token",
    "auth",
    "authtoken",
    "jwt",
    "access_token",
    "user_session",
}


class CookieSecurityAnalyzer:
    """Audits cookie flags and privacy attributes with strict value redaction."""

    def analyze(self, page_records: list[SecurityPageRecord]) -> CookieSecurityAssessment:
        """Parse Set-Cookie headers and recorded cookie objects."""
        records: list[CookieAttributeRecord] = []
        seen_names: set[str] = set()

        for idx, page in enumerate(page_records, start=1):
            # 1. From page.cookies dictionary/list
            for c in page.cookies:
                name = c.get("name", "").strip()
                if not name or name in seen_names:
                    continue
                seen_names.add(name)
                records.append(self._parse_cookie_dict(c, f"ev-cookie-{name}-p{idx}"))

            # 2. From page.headers 'set-cookie'
            set_cookie_raw = page.headers.get("set-cookie", "")
            if set_cookie_raw and "[REDACTED" not in set_cookie_raw:
                # Can have multiple cookies separated by commas or lines
                for line in set_cookie_raw.splitlines():
                    record = self._parse_set_cookie_header(line, f"ev-setcookie-p{idx}")
                    if record and record.name not in seen_names:
                        seen_names.add(record.name)
                        records.append(record)

        total = len(records)
        secure_count = sum(1 for r in records if r.is_secure)
        http_only_count = sum(1 for r in records if r.is_http_only)
        same_site_count = sum(1 for r in records if r.same_site and r.same_site != "Unknown")
        same_site_none_insecure = sum(1 for r in records if r.same_site == "None" and not r.is_secure)
        session_missing_flags = sum(1 for r in records if r.is_session and (not r.is_secure or not r.is_http_only))

        evidence_ids = [f"ev-cookie-audit-{len(records)}"] if records else []

        notes = (
            f"Observed {total} cookies across pages. "
            f"Secure: {secure_count}/{total}, HttpOnly: {http_only_count}/{total}, "
            f"Configured SameSite: {same_site_count}/{total}. "
            + (
                f"Warning: {same_site_none_insecure} cookies have SameSite=None without Secure! "
                if same_site_none_insecure
                else ""
            )
            + (
                f"Warning: {session_missing_flags} apparent session cookies lack defensive flags."
                if session_missing_flags
                else ""
            )
        )
        notes_ar = (
            f"تم رصد {total} ملف ارتباط (كوكيز). "
            f"المحمي بـ Secure: {secure_count}/{total}، المحمي بـ HttpOnly: {http_only_count}/{total}، "
            f"المحدد بـ SameSite: {same_site_count}/{total}. "
            + (
                f"تنبيه: {same_site_none_insecure} ملف ارتباط يحمل SameSite=None دون تفعيل Secure! "
                if same_site_none_insecure
                else ""
            )
            + (
                f"تنبيه: {session_missing_flags} ملف ارتباط قد يخص الجلسات يفتقر لسمات الحماية."
                if session_missing_flags
                else ""
            )
        )

        return CookieSecurityAssessment(
            total_cookies_observed=total,
            secure_cookies_count=secure_count,
            http_only_cookies_count=http_only_count,
            same_site_configured_count=same_site_count,
            same_site_none_insecure_count=same_site_none_insecure,
            apparent_session_cookies_missing_flags=session_missing_flags,
            cookie_records=records,
            evidence_ids=evidence_ids,
            notes=notes,
            notes_ar=notes_ar,
        )

    def _parse_cookie_dict(self, c: dict[str, Any], ev_id: str) -> CookieAttributeRecord:
        name = c.get("name", "")
        domain = c.get("domain")
        path = c.get("path", "/")
        is_secure = bool(c.get("secure", False))
        is_http_only = bool(c.get("httpOnly", False) or c.get("httponly", False))

        raw_ss = str(c.get("sameSite", "")).lower()
        same_site = "Unknown"
        if "strict" in raw_ss:
            same_site = "Strict"
        elif "lax" in raw_ss:
            same_site = "Lax"
        elif "none" in raw_ss:
            same_site = "None"

        is_session = self._is_likely_session(name)
        has_prefix = name.startswith("__Secure-") or name.startswith("__Host-")

        risk_flags: list[str] = []
        risk_flags_ar: list[str] = []

        if same_site == "None" and not is_secure:
            risk_flags.append("SameSite=None requires Secure attribute in modern browsers.")
            risk_flags_ar.append("خاصية SameSite=None تتطلب تفعيل Secure في المتصفحات الحديثة.")

        if is_session:
            if not is_secure:
                risk_flags.append("Session cookie transmitted over unencrypted transport (missing Secure).")
                risk_flags_ar.append("ملف جلسة يتم نقله بدون تشفير (غياب خاصية Secure).")
            if not is_http_only:
                risk_flags.append("Session cookie accessible to client-side scripts (missing HttpOnly).")
                risk_flags_ar.append("ملف جلسة متاح للسكربتات عبر المتصفح (غياب خاصية HttpOnly).")

        return CookieAttributeRecord(
            name=name,
            domain=domain,
            path=path,
            is_secure=is_secure,
            is_http_only=is_http_only,
            same_site=same_site,  # type: ignore
            is_session=is_session,
            apparent_purpose="session_auth" if is_session else "functional_preferences",
            has_secure_prefix=has_prefix,
            expires=str(c.get("expires")) if c.get("expires") else None,
            max_age=int(c.get("maxAge")) if c.get("maxAge") is not None else None,
            risk_flags=risk_flags,
            risk_flags_ar=risk_flags_ar,
        )

    def _parse_set_cookie_header(self, raw_header: str, ev_id: str) -> Optional[CookieAttributeRecord]:
        parts = raw_header.split(";")
        if not parts:
            return None
        first = parts[0].strip()
        if "=" not in first:
            return None
        name, _ = first.split("=", 1)
        name = name.strip()

        attrs = [p.strip().lower() for p in parts[1:]]
        is_secure = "secure" in attrs
        is_http_only = "httponly" in attrs

        same_site = "Unknown"
        for a in attrs:
            if a.startswith("samesite="):
                val = a.split("=", 1)[1].strip()
                if val == "strict":
                    same_site = "Strict"
                elif val == "lax":
                    same_site = "Lax"
                elif val == "none":
                    same_site = "None"

        domain = None
        for a in attrs:
            if a.startswith("domain="):
                domain = a.split("=", 1)[1].strip()

        path = "/"
        for a in attrs:
            if a.startswith("path="):
                path = a.split("=", 1)[1].strip()

        is_session = self._is_likely_session(name)
        has_prefix = name.startswith("__Secure-") or name.startswith("__Host-")

        risk_flags: list[str] = []
        risk_flags_ar: list[str] = []

        if same_site == "None" and not is_secure:
            risk_flags.append("SameSite=None requires Secure attribute.")
            risk_flags_ar.append("خاصية SameSite=None تتطلب تفعيل Secure.")

        if is_session:
            if not is_secure:
                risk_flags.append("Session cookie missing Secure attribute.")
                risk_flags_ar.append("ملف جلسة يفتقر لخاصية Secure.")
            if not is_http_only:
                risk_flags.append("Session cookie missing HttpOnly attribute.")
                risk_flags_ar.append("ملف جلسة يفتقر لخاصية HttpOnly.")

        return CookieAttributeRecord(
            name=name,
            domain=domain,
            path=path,
            is_secure=is_secure,
            is_http_only=is_http_only,
            same_site=same_site,  # type: ignore
            is_session=is_session,
            apparent_purpose="session_auth" if is_session else "unknown",
            has_secure_prefix=has_prefix,
            risk_flags=risk_flags,
            risk_flags_ar=risk_flags_ar,
        )

    def _is_likely_session(self, name: str) -> bool:
        clean = re.sub(r"[_\-]", "", name.lower())
        return any(s in clean for s in ("session", "auth", "token", "jwt", "phpsessid", "jsessionid"))
