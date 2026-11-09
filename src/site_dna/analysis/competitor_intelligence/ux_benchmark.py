"""UX and Usability Benchmarking Engine for Site DNA Phase 08."""

from typing import Any

from site_dna.core.logging import get_logger
from site_dna.schemas.competitor_intelligence import CompetitorSourceRecord, UXBenchmark

logger = get_logger("analysis.competitor_intelligence.ux_benchmark")


class UXBenchmarkAnalyzer:
    """Benchmarks navigation clarity, CTA discoverability, and accessibility findings."""

    def compare_ux(
        self,
        primary_site: CompetitorSourceRecord,
        competitor_sites: list[CompetitorSourceRecord],
        ux_dataset: dict[str, dict[str, Any]],
    ) -> list[UXBenchmark]:
        """Produce structured UX benchmarks based on verified UX observations."""
        benchmarks: list[UXBenchmark] = []

        dimensions = [
            (
                "Navigation Architecture & Information Flow",
                "navigation",
                ["Clear primary menu", "Logical depth hierarchy"],
            ),
            ("Call-to-Action (CTA) Discoverability", "cta", ["Contrasting primary button", "Reduced choice friction"]),
            ("Form Ergonomics & Interaction", "forms", ["Inline validation", "Minimal required inputs"]),
            (
                "Accessibility & Touch Target Sizing",
                "accessibility",
                ["WCAG AA color contrast", "44px min tap targets"],
            ),
        ]

        for dim, key, patterns in dimensions:
            p_count = len(ux_dataset.get(primary_site.site_id, {}).get(f"{key}_findings", []))
            c_counts: dict[str, int] = {}
            for comp in competitor_sites:
                c_counts[comp.site_id] = len(ux_dataset.get(comp.site_id, {}).get(f"{key}_findings", []))

            benchmarks.append(
                UXBenchmark(
                    dimension=dim,
                    primary_findings_count=p_count,
                    competitor_findings_counts=c_counts,
                    observed_patterns=patterns,
                )
            )

        return benchmarks
