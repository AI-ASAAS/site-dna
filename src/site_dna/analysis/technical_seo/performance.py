"""Website performance measurement and laboratory timing analysis engine."""

from typing import Optional

from site_dna.schemas.discovery import CrawlResult
from site_dna.schemas.technical_seo import (
    PerformanceMeasurement,
    TechnicalPageRecord,
    TechnicalSEOFinding,
)
from site_dna.schemas.visual import VisualCaptureResult


class PerformanceAnalyzer:
    """Evaluates response durations, document sizes, and resource request volume."""

    @staticmethod
    def analyze(
        pages: list[TechnicalPageRecord],
        crawl_result: CrawlResult,
        visual_result: Optional[VisualCaptureResult],
    ) -> tuple[list[PerformanceMeasurement], list[TechnicalSEOFinding]]:
        """Extract and evaluate measured performance parameters."""
        measurements: list[PerformanceMeasurement] = []
        findings: list[TechnicalSEOFinding] = []
        if not pages:
            return measurements, findings

        evidence_ids = pages[0].source_evidence_ids[:3]

        # 1. Total crawl fetch duration and document size
        total_duration = crawl_result.statistics.total_duration_ms
        total_bytes = crawl_result.statistics.total_bytes_fetched
        page_count = max(1, crawl_result.statistics.total_pages_crawled)
        avg_fetch_ms = total_duration / page_count

        # Record TTFB / fetch timing measurement
        measurements.append(
            PerformanceMeasurement(
                metric_name="average_fetch_duration",
                value=round(avg_fetch_ms, 2),
                unit="ms",
                source="navigation_timing",
                measurement_type="local_browser",
                conditions={"pages_sampled": page_count, "concurrency": 1},
                limitations=["Laboratory measurement from single collector location; not field RUM."],
            )
        )

        # Record document size
        measurements.append(
            PerformanceMeasurement(
                metric_name="total_html_transfer_size",
                value=float(total_bytes),
                unit="bytes",
                source="navigation_timing",
                measurement_type="local_browser",
                conditions={"pages_sampled": page_count},
                limitations=["Represents raw HTML body size, excluding external CDN subresources."],
            )
        )

        # Check for slow server response / TTFB warning (> 1200ms)
        if avg_fetch_ms > 1200:
            findings.append(
                TechnicalSEOFinding(
                    finding_id="TS-PRF-SLOW-TTFB",
                    title="زمن استجابة أولي بطيء من الخادم TTFB (Slow Server Response Time)",
                    category="performance",
                    description=f"متوسط زمن جلب الصفحات الأولي ({round(avg_fetch_ms, 1)} ms) يتجاوز الحد الموصى به (أقل من 800 ms).",
                    page_url=pages[0].requested_url,
                    evidence_ids=evidence_ids,
                    observation_type="external_measurement",
                    severity="high",
                    confidence_category="measured",
                    potential_technical_impact="تأخر عرض المحتوى (LCP) وارتفاع معدل ارتداد الزوار وتأثير سلبي على زحف محركات البحث.",
                    recommended_action="تفعيل التخزين المؤقت على الخادم (Server Caching)، واستخدام شبكة توزيع محتوى (CDN)، وتحسين استعلامات قواعد البيانات.",
                )
            )

        # Check for excessive document size (> 2 MB)
        if total_bytes / page_count > 2_000_000:
            findings.append(
                TechnicalSEOFinding(
                    finding_id="TS-PRF-LARGE-DOM",
                    title="حجم مفرط لملف HTML المصدري (Excessive Document Payload Size)",
                    category="performance",
                    description=f"متوسط حجم كود HTML ({round(total_bytes / (page_count * 1024), 1)} KB) كبير جداً ويتجاوز الحدود المقبولة.",
                    page_url=pages[0].requested_url,
                    evidence_ids=evidence_ids,
                    observation_type="external_measurement",
                    severity="medium",
                    confidence_category="measured",
                    potential_technical_impact="بطء معالجة وتحليل الـ DOM في أجهزة الهواتف واستهلاك باقات بيانات المستخدمين.",
                    recommended_action="تقليل حجم ملف الـ HTML وإزالة النصوص والأنماط المضمنة الضخمة وضغط النقل عبر Gzip / Brotli.",
                )
            )

        # Visual capture duration if available
        if visual_result:
            vis_ms = visual_result.statistics.total_duration_ms
            measurements.append(
                PerformanceMeasurement(
                    metric_name="playwright_render_duration",
                    value=round(vis_ms, 2),
                    unit="ms",
                    source="playwright_collector",
                    measurement_type="laboratory",
                    conditions={"browser": "chromium", "headless": True},
                    limitations=["Includes full Playwright automation overhead and screenshot generation time."],
                )
            )

        return measurements, findings
