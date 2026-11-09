"""Content Security Policy (CSP) Analyzer for Site DNA Phase 09."""

import re

from site_dna.schemas.security_privacy import (
    CSPAssessment,
    SecurityPageRecord,
)


class CSPAnalyzer:
    """Parses and audits Content Security Policy headers for defensive rigor."""

    def analyze(self, page_records: list[SecurityPageRecord]) -> CSPAssessment:
        """Examine CSP directives from response headers."""
        if not page_records:
            return CSPAssessment(
                notes="No pages available to assess Content Security Policy.",
                notes_ar="لا تتوفر صفحات لفحص سياسة أمان المحتوى.",
            )

        # Look for CSP headers across pages
        raw_csp: str = ""
        is_report_only = False
        evidence_ids: list[str] = []

        for idx, page in enumerate(page_records, start=1):
            headers = page.headers
            if "content-security-policy" in headers:
                raw_csp = headers["content-security-policy"]
                evidence_ids.append(f"ev-csp-enforced-p{idx}")
                break
            elif "content-security-policy-report-only" in headers:
                raw_csp = headers["content-security-policy-report-only"]
                is_report_only = True
                evidence_ids.append(f"ev-csp-reportonly-p{idx}")
                break

        if not raw_csp:
            return CSPAssessment(
                is_enforced=False,
                is_report_only=False,
                raw_policy=None,
                defense_in_depth_score=0.0,
                notes="No Content Security Policy header observed on inspected responses.",
                notes_ar="لم يتم رصد أي ترويسة لسياسة أمان المحتوى (CSP) في الردود المفحوصة.",
            )

        # Parse directives
        directives: dict[str, list[str]] = {}
        tokens = raw_csp.split(";")
        for token in tokens:
            parts = token.strip().split()
            if parts:
                dir_name = parts[0].lower()
                dir_sources = [s.lower() for s in parts[1:]]
                directives[dir_name] = dir_sources

        has_default = "default-src" in directives
        has_script = "script-src" in directives
        has_object = "object-src" in directives
        has_base = "base-uri" in directives
        has_frame = "frame-ancestors" in directives

        # Evaluate risk flags
        raw_lower = raw_csp.lower()
        allows_inline = "'unsafe-inline'" in raw_lower
        allows_eval = "'unsafe-eval'" in raw_lower
        allows_wildcards = bool(re.search(r"(?:default-src|script-src)[^;]*\s+\*", raw_csp))

        # Calculate defense-in-depth score (0 to 100)
        score = 0.0
        if not is_report_only:
            score += 20.0  # Enforced policy baseline
        else:
            score += 10.0  # Report-only baseline

        if has_default:
            score += 20.0
        if has_script:
            score += 15.0
        if has_object:
            score += 15.0
        if has_base:
            score += 10.0
        if has_frame:
            score += 10.0

        if allows_inline:
            score -= 15.0
        if allows_eval:
            score -= 10.0
        if allows_wildcards:
            score -= 15.0

        score = max(0.0, min(100.0, score))

        notes = (
            f"CSP is {'Report-Only' if is_report_only else 'Enforced'}. "
            f"Directives found: {len(directives)}. "
            + ("Allows 'unsafe-inline'. " if allows_inline else "")
            + ("Allows 'unsafe-eval'. " if allows_eval else "")
            + ("Contains broad wildcards. " if allows_wildcards else "")
        )
        notes_ar = (
            f"سياسة CSP في وضع {'التقرير فقط (Report-Only)' if is_report_only else 'التنفيذ الإجباري (Enforced)'}. "
            f"عدد التعليمات المعرفة: {len(directives)}. "
            + ("تسمح بتنفيذ السكربتات المضمنة 'unsafe-inline'. " if allows_inline else "")
            + ("تسمح بدوال التقييم الديناميكي 'unsafe-eval'. " if allows_eval else "")
            + ("تحتوي على محارف تعميم واسعة '*'. " if allows_wildcards else "")
        )

        return CSPAssessment(
            is_enforced=not is_report_only,
            is_report_only=is_report_only,
            raw_policy=raw_csp[:500],
            directives=directives,
            has_default_src=has_default,
            has_script_src=has_script,
            has_object_src=has_object,
            has_base_uri=has_base,
            has_frame_ancestors=has_frame,
            allows_unsafe_inline=allows_inline,
            allows_unsafe_eval=allows_eval,
            allows_broad_wildcards=allows_wildcards,
            defense_in_depth_score=score,
            evidence_ids=evidence_ids,
            notes=notes,
            notes_ar=notes_ar,
        )
