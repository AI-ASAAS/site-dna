"""Client-Side Structure and Script Observation Analyzer for Site DNA Phase 09."""

import re
from typing import Any, Optional

from site_dna.schemas.security_privacy import (
    ClientSideObservation,
    SecurityPageRecord,
)


class ClientSideObservationsAnalyzer:
    """Analyzes inline scripts, SRI integrity tags, and external dependency patterns."""

    def analyze(
        self,
        page_records: list[SecurityPageRecord],
        crawl_dataset: Optional[dict[str, Any]] = None,
    ) -> ClientSideObservation:
        """Examine client-side DOM and scripts passively."""
        if not page_records:
            return ClientSideObservation(
                notes="No pages available to assess client-side scripts.",
                notes_ar="لا تتوفر صفحات لفحص السكربتات المضمنة والاعتماديات.",
            )

        total_inline = 0
        total_external = 0
        with_sri = 0
        lacking_sri = 0
        frameworks: list[dict[str, str]] = []
        unsafe_patterns: list[str] = []
        seen_scripts: set[str] = set()

        for idx, page in enumerate(page_records, start=1):
            # Inspect HTML content from crawl_dataset if available
            p_data = (crawl_dataset or {}).get("pages", [])
            matched = next((p for p in p_data if p.get("url") == page.page_url), None)
            html = (matched.get("raw_html") or matched.get("html") or "") if matched else ""

            if not html:
                continue

            # 1. Inline scripts (<script> without src)
            inline_matches = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.DOTALL | re.IGNORECASE)
            total_inline += len(inline_matches)

            # 2. External scripts (<script src="...">)
            external_matches = re.finditer(r"""<script[^>]*\bsrc=['"]([^'"]+)['"][^>]*>""", html, re.IGNORECASE)
            for m in external_matches:
                tag_str = m.group(0)
                src = m.group(1).split("?")[0]
                if src in seen_scripts:
                    continue
                seen_scripts.add(src)
                total_external += 1

                # Check Subresource Integrity (SRI)
                if "integrity=" in tag_str.lower():
                    with_sri += 1
                else:
                    lacking_sri += 1

            # 3. Detect framework indicators in HTML
            if "react" in html.lower() and not any(f["name"] == "React" for f in frameworks):
                frameworks.append({"name": "React", "version": "detected_in_bundle"})
            if "next" in html.lower() and not any(f["name"] == "Next.js" for f in frameworks):
                frameworks.append({"name": "Next.js", "version": "detected_in_build"})
            if "vue" in html.lower() and not any(f["name"] == "Vue.js" for f in frameworks):
                frameworks.append({"name": "Vue.js", "version": "detected_in_bundle"})

            # Check for document.write or eval patterns
            if "document.write" in html.lower() and "document.write" not in unsafe_patterns:
                unsafe_patterns.append("document.write() pattern observed in HTML")
            if "eval(" in html.lower() and "eval()" not in unsafe_patterns:
                unsafe_patterns.append("eval() pattern observed in script blocks")

        evidence_ids = ["ev-client-scripts"] if total_external or total_inline else []

        notes = (
            f"Observed {total_inline} inline scripts and {total_external} external scripts. "
            f"SRI Protection: {with_sri} with SRI, {lacking_sri} without SRI."
        )
        notes_ar = (
            f"تم رصد {total_inline} سكربت مضمن (inline) و {total_external} سكربت خارجي. "
            f"حماية تكامل الموارد (SRI): {with_sri} يحمل سمة integrity، و {lacking_sri} يفتقر لها."
        )

        return ClientSideObservation(
            inline_scripts_count=total_inline,
            external_scripts_count=total_external,
            scripts_with_sri_count=with_sri,
            scripts_lacking_sri_count=lacking_sri,
            frameworks_detected=frameworks,
            has_unpinned_external_scripts=lacking_sri > 0,
            unsafe_patterns_observed=unsafe_patterns,
            evidence_ids=evidence_ids,
            notes=notes,
            notes_ar=notes_ar,
        )
