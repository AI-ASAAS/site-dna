"""Representative Page Sampling Engine for Site DNA Phase 10 (WCAG-EM Step 3)."""

from typing import Optional
from urllib.parse import urlsplit

from site_dna.schemas.accessibility import (
    AccessibilityPageRecord,
    AccessibilitySamplingRecord,
)


class RepresentativeSampler:
    """Selects a bounded, representative sample of web pages for WCAG 2.2 evaluation."""

    def select_sample(
        self,
        pages: list[AccessibilityPageRecord],
        max_pages: int = 8,
    ) -> AccessibilitySamplingRecord:
        """Select up to max_pages based on functional variety and interaction density."""
        if not pages:
            return AccessibilitySamplingRecord(
                sampled_pages_count=0,
                total_pages_discovered=0,
                sampled_pages=[],
                selection_strategy="empty",
                excluded_pages_count=0,
                coverage_limitations=["No pages available in crawl dataset."],
                coverage_limitations_ar=["لا توجد أي صفحات مسجلة في مجموعة بيانات الزحف."],
            )

        total_pages = len(pages)
        if total_pages <= max_pages:
            for p in pages:
                p.is_representative_sample = True
                p.sample_reason = "Complete enumeration of small crawl set"

            return AccessibilitySamplingRecord(
                sampled_pages_count=total_pages,
                total_pages_discovered=total_pages,
                sampled_pages=pages,
                selection_strategy="complete_enumeration",
                excluded_pages_count=0,
                coverage_limitations=[
                    f"Sample covers all {total_pages} discovered pages; dynamic unlinked states require manual audit."
                ],
                coverage_limitations_ar=[
                    f"تغطي العينة جميع الصفحات المكتشفة البالغ عددها {total_pages} صفحة؛ الحالات الديناميكية غير المرتبطة تتطلب تدقيقاً يدوياً."
                ],
            )

        # Priority buckets for representative variety
        selected: list[AccessibilityPageRecord] = []
        selected_urls: set[str] = set()

        def add_candidate(candidate: AccessibilityPageRecord, reason: str) -> bool:
            if len(selected) >= max_pages:
                return False
            if candidate.page_url not in selected_urls:
                candidate.is_representative_sample = True
                candidate.sample_reason = reason
                selected.append(candidate)
                selected_urls.add(candidate.page_url)
                return True
            return False

        # 1. Homepage / Root page
        for p in pages:
            path = urlsplit(p.page_url).path.strip("/")
            if not path or path in ("index.html", "index.php", "home"):
                add_candidate(p, "Homepage / Primary Entry Point")
                break

        # 2. Page with highest form controls count (Contact / Auth / Lead form)
        form_pages = sorted(
            [p for p in pages if p.form_controls_count > 0],
            key=lambda x: x.form_controls_count,
            reverse=True,
        )
        for p in form_pages:
            if add_candidate(p, f"Form / Transactional interface ({p.form_controls_count} controls)"):
                break

        # 3. Page with highest interactive density (Navigation / Dashboard / App view)
        interactive_pages = sorted(
            pages,
            key=lambda x: x.interactive_elements_count,
            reverse=True,
        )
        for p in interactive_pages:
            if add_candidate(p, f"High interactive density ({p.interactive_elements_count} elements)"):
                break

        # 4. Content / Article / Text page (highest headings count)
        content_pages = sorted(
            pages,
            key=lambda x: x.headings_count,
            reverse=True,
        )
        for p in content_pages:
            if add_candidate(p, f"Content-heavy structure ({p.headings_count} headings)"):
                break

        # 5. Media-rich page (highest images count)
        media_pages = sorted(
            pages,
            key=lambda x: x.images_count,
            reverse=True,
        )
        for p in media_pages:
            if add_candidate(p, f"Media-rich presentation ({p.images_count} images)"):
                break

        # 6. Fill remaining slots with distinct functional paths
        for p in pages:
            if len(selected) >= max_pages:
                break
            add_candidate(p, "General representative functional path")

        excluded_count = total_pages - len(selected)
        return AccessibilitySamplingRecord(
            sampled_pages_count=len(selected),
            total_pages_discovered=total_pages,
            sampled_pages=selected,
            selection_strategy="wcag_em_structured_heuristics",
            excluded_pages_count=excluded_count,
            coverage_limitations=[
                f"Sample of {len(selected)} pages selected from {total_pages} discovered URLs.",
                "Automated sample does not constitute a full site-wide WCAG conformance certification.",
                f"{excluded_count} pages were not evaluated in this bounded run.",
            ],
            coverage_limitations_ar=[
                f"تم اختيار عينة ممثلة من {len(selected)} صفحة من أصل {total_pages} رابط تم اكتشافه.",
                "العينة الآلية لا تمثل شهادة مطابقة شاملة للموقع بالكامل لمعايير WCAG.",
                f"هناك {excluded_count} صفحة لم يتم تقييمها في هذه الجولة المحدودة.",
            ],
        )


class AccessibilitySampler(RepresentativeSampler):
    """Convenience alias for test compatibility."""

    def __init__(self, max_pages: int = 8):
        self.default_max_pages = max_pages

    def sample_pages(
        self,
        pages: list[AccessibilityPageRecord],
        total_discovered: Optional[int] = None,
    ) -> AccessibilitySamplingRecord:
        record = self.select_sample(pages, max_pages=self.default_max_pages)
        if total_discovered is not None:
            record.total_pages_discovered = total_discovered
        return record
