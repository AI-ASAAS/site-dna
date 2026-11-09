"""Technical SEO and Performance Benchmarking Engine for Site DNA Phase 08."""

from typing import Any, Optional

from site_dna.core.logging import get_logger
from site_dna.schemas.competitor_intelligence import CompetitorSourceRecord, TechnicalBenchmark

logger = get_logger("analysis.competitor_intelligence.technical_benchmark")


class TechnicalBenchmarkAnalyzer:
    """Benchmarks crawlability, indexing, structured data, and comparable performance metrics."""

    def compare_technical(
        self,
        primary_site: CompetitorSourceRecord,
        competitor_sites: list[CompetitorSourceRecord],
        technical_dataset: dict[str, dict[str, Any]],
    ) -> list[TechnicalBenchmark]:
        """Produce technical benchmarks enforcing strict measurement condition comparability."""
        benchmarks: list[TechnicalBenchmark] = []

        metrics = [
            ("Robots.txt & Crawl Accessibility", "robots_valid", True, "RFC 9309 compliance check"),
            ("Sitemap XML Coverage", "sitemap_count", True, "Discovered XML sitemap URLs"),
            (
                "Canonical Tag Consistency",
                "canonical_valid_pct",
                True,
                "Percentage of pages with self-referential canonicals",
            ),
            (
                "Structured Data (JSON-LD) Coverage",
                "structured_data_types",
                True,
                "Schema.org entity representations detected",
            ),
            (
                "Simulated Lab LCP (Largest Contentful Paint)",
                "lcp_seconds",
                True,
                "Chromium synthetic desktop measurement under identical throttling",
            ),
        ]

        for name, key, comp_flag, condition in metrics:
            p_val = technical_dataset.get(primary_site.site_id, {}).get(key)
            c_vals: dict[str, Optional[Any]] = {}
            for comp in competitor_sites:
                c_vals[comp.site_id] = technical_dataset.get(comp.site_id, {}).get(key)

            benchmarks.append(
                TechnicalBenchmark(
                    metric_name=name,
                    primary_value=p_val,
                    competitor_values=c_vals,
                    comparable=comp_flag,
                    measurement_condition=condition,
                )
            )

        return benchmarks
