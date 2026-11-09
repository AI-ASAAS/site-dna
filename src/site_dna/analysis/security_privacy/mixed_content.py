"""Mixed Content Analyzer for Site DNA Phase 09."""

from site_dna.schemas.security_privacy import (
    MixedContentAssessment,
    MixedContentRecord,
    SecurityPageRecord,
)


class MixedContentAnalyzer:
    """Evaluates mixed content risks on HTTPS pages."""

    def analyze(self, page_records: list[SecurityPageRecord]) -> MixedContentAssessment:
        """Scan inspected pages for insecure HTTP references."""
        records: list[MixedContentRecord] = []
        seen_urls: set[str] = set()

        for idx, page in enumerate(page_records, start=1):
            if page.scheme.lower() != "https":
                continue

            for raw_res in page.mixed_content_resources:
                # Strip query strings safely
                clean_url = raw_res.split("?")[0].split("#")[0]
                if clean_url in seen_urls:
                    continue
                seen_urls.add(clean_url)

                res_type = "unknown"
                lower = clean_url.lower()
                if lower.endswith((".js", ".mjs")):
                    res_type = "script"
                elif lower.endswith(".css"):
                    res_type = "stylesheet"
                elif lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico")):
                    res_type = "image"
                elif lower.endswith((".mp4", ".webm", ".mp3", ".ogg")):
                    res_type = "media"

                records.append(
                    MixedContentRecord(
                        page_url=page.page_url,
                        insecure_resource_url=clean_url[:200],
                        resource_type=res_type,  # type: ignore
                        disposition="observed_insecure",
                        evidence_ids=[f"ev-mixed-res-p{idx}"],
                    )
                )

        has_mixed = len(records) > 0
        insecure_count = len(records)
        evidence_ids = [f"ev-mixed-{len(records)}"] if records else []

        notes = (
            f"Observed {insecure_count} insecure HTTP resource references across HTTPS pages."
            if has_mixed
            else "No insecure mixed-content references observed in the inspected sample."
        )
        notes_ar = (
            f"تم رصد {insecure_count} مورد يعمل بروتوكول HTTP غير مشفر ضمن صفحات HTTPS."
            if has_mixed
            else "لم يتم رصد أي موارد محتوى مختلط غير مشفرة في عينة الصفحات المفحوصة."
        )

        return MixedContentAssessment(
            has_mixed_content=has_mixed,
            insecure_references_count=insecure_count,
            blocked_references_count=0,
            upgraded_references_count=0,
            records=records,
            evidence_ids=evidence_ids,
            notes=notes,
            notes_ar=notes_ar,
        )
