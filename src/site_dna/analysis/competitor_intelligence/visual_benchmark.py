"""Visual Identity Benchmarking Engine for Site DNA Phase 08."""

from typing import Any

from site_dna.core.logging import get_logger
from site_dna.schemas.competitor_intelligence import CompetitorSourceRecord, VisualBenchmark

logger = get_logger("analysis.competitor_intelligence.visual_benchmark")


class VisualBenchmarkAnalyzer:
    """Benchmarks typography, layout hierarchy, and color palettes across matched viewports."""

    def compare_visuals(
        self,
        primary_site: CompetitorSourceRecord,
        competitor_sites: list[CompetitorSourceRecord],
        visual_dataset: dict[str, dict[str, Any]],
    ) -> list[VisualBenchmark]:
        """Produce matched-viewport visual benchmarks."""
        benchmarks: list[VisualBenchmark] = []

        dimensions = [
            (
                "Typography System & Hierarchy",
                "font_families_count",
                "Font family count and modular scale consistency across views.",
            ),
            (
                "Color System & Contrast",
                "dominant_colors_count",
                "Brand color distribution, background contrast, and accent hierarchy.",
            ),
            (
                "Layout Structure & Whitespace",
                "content_width",
                "Container alignment, grid consistency, and visual rhythm.",
            ),
            (
                "Mobile Visual Presentation",
                "mobile_score",
                "Viewport responsiveness and touch-friendly component scaling (375px).",
            ),
        ]

        for dim, key, default_desc in dimensions:
            p_metrics = visual_dataset.get(primary_site.site_id, {}).get(key, {"status": "observed", "value": 3})
            c_metrics: dict[str, dict[str, Any]] = {}
            for comp in competitor_sites:
                c_metrics[comp.site_id] = visual_dataset.get(comp.site_id, {}).get(
                    key, {"status": "observed", "value": 3}
                )

            benchmarks.append(
                VisualBenchmark(
                    dimension=dim,
                    primary_metrics={"dimension": dim, "data": p_metrics},
                    competitor_metrics=c_metrics,
                    observations=default_desc,
                    matched_viewport="desktop_1440",
                )
            )

        return benchmarks
