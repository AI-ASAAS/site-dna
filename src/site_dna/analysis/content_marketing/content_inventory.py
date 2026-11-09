"""Structured content inventory builder for Site DNA Content & Marketing Intelligence."""

from site_dna.analysis.content_marketing.page_classifier import PageClassifier
from site_dna.schemas.content_marketing import ContentInventory, PageContentRecord


class ContentInventoryBuilder:
    """Builds an aggregated content inventory across all analyzed pages."""

    @staticmethod
    def build_inventory(pages: list[PageContentRecord]) -> ContentInventory:
        """Process page records and return a comprehensive ContentInventory."""
        if not pages:
            return ContentInventory()

        distribution: dict[str, int] = {}
        total_words = 0
        languages = set()
        missing_descriptions = 0
        headings_counts: dict[str, int] = {"h1": 0, "h2": 0, "h3": 0, "h4": 0, "h5": 0, "h6": 0}

        for p in pages:
            # Refine classification
            p.page_type = PageClassifier.classify_page(p)
            distribution[p.page_type] = distribution.get(p.page_type, 0) + 1

            total_words += p.word_count

            if p.language:
                languages.add(p.language.lower()[:2])

            if not p.meta_description or not p.meta_description.strip():
                missing_descriptions += 1

            for h in p.headings:
                lvl = f"h{h.get('level', 1)}"
                headings_counts[lvl] = headings_counts.get(lvl, 0) + 1

        avg_words = round(total_words / len(pages), 1) if pages else 0.0

        return ContentInventory(
            total_pages=len(pages),
            page_types_distribution=distribution,
            total_word_count=total_words,
            average_word_count_per_page=avg_words,
            languages_detected=sorted(list(languages)),
            pages=pages,
            missing_descriptions_count=missing_descriptions,
            headings_summary=headings_counts,
        )
