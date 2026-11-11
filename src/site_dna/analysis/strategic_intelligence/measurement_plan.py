"""Measurement Plan Generator for Site DNA Phase 11."""


from site_dna.schemas.strategic_intelligence import MeasurementPlan, UnifiedFinding


class MeasurementPlanner:
    """Generates measurable outcome metrics with strict null-baseline handling."""

    def build_measurement_plan(self, findings: list[UnifiedFinding]) -> list[MeasurementPlan]:
        """Define empirical metrics to monitor progress post-implementation."""
        metrics: list[MeasurementPlan] = []

        # Metric 1: Confirmed Accessibility Barriers
        a11y_count = sum(
            1 for f in findings if f.source_phase == "accessibility" and f.verification_state == "confirmed_by_evidence"
        )
        metrics.append(
            MeasurementPlan(
                name="Confirmed Accessibility Barriers (WCAG 2.2)",
                name_ar="حواجز النفاذ الرقمي المؤكدة (WCAG 2.2)",
                purpose="Track reduction of deterministic accessibility blockers across key pages.",
                data_source="Site DNA Accessibility Analyzer",
                baseline_value=float(a11y_count),
                baseline_status="available",
                target_value=0.0,
                target_status="user_configured",
                measurement_method="Automated WCAG 2.2 DOM and CSS audit.",
                measurement_frequency="Per sprint release",
                limitations="Measures automated criteria only; human screen reader checks required for complete coverage.",
            )
        )

        # Metric 2: Security Header Defense-in-Depth Posture
        sec_header_count = sum(
            1
            for f in findings
            if f.source_phase == "security_privacy"
            and "header" in (f.title + f.category).lower()
            and f.verification_state == "confirmed_by_evidence"
        )
        metrics.append(
            MeasurementPlan(
                name="Missing Core Security Headers",
                name_ar="ترويسات الأمان المفقودة",
                purpose="Ensure 100% deployment of mandatory defensive HTTP transport headers.",
                data_source="Site DNA Security & Privacy Analyzer",
                baseline_value=float(sec_header_count),
                baseline_status="available",
                target_value=0.0,
                target_status="user_configured",
                measurement_method="Live HTTP response header verification across edge endpoints.",
                measurement_frequency="Continuous / on deployment",
                limitations="Checks observable response headers; does not evaluate internal network segmentations.",
            )
        )

        # Metric 3: Broken Links & Crawl Traps
        broken_links_count = sum(
            1
            for f in findings
            if f.source_phase in ("technical_seo", "ux_ui")
            and any(term in (f.title + f.description).lower() for term in ("broken", "404", "معطل"))
        )
        metrics.append(
            MeasurementPlan(
                name="Broken Internal Links & Redirection Traps",
                name_ar="الروابط الداخلية المعطلة وفخاخ إعادة التوجيه",
                purpose="Maintain zero 4xx/5xx crawl traps to preserve crawl budget and user flow continuity.",
                data_source="Site DNA Technical SEO Crawler",
                baseline_value=float(broken_links_count),
                baseline_status="available",
                target_value=0.0,
                target_status="user_configured",
                measurement_method="Full-site internal link graph extraction.",
                measurement_frequency="Weekly",
                limitations="Does not track external third-party destination health beyond target origin bounds.",
            )
        )

        # Metric 4: Form Conversion Completion Rate (Null Baseline until client analytics connected)
        metrics.append(
            MeasurementPlan(
                name="Form Submission Completion Rate",
                name_ar="معدل إكمال النماذج التفاعلية",
                purpose="Empirically evaluate reduction in user drop-off after form UX label remediation.",
                data_source="Authorized Web Analytics (e.g. Google Analytics / PostHog)",
                baseline_value=None,
                baseline_status="null_baseline",
                target_value=None,
                target_status="not_set",
                measurement_method="Funnel step-through telemetry on contact and checkout forms.",
                measurement_frequency="Monthly cohort comparison",
                limitations="Requires client-side analytics integration; cannot be computed from passive crawling alone.",
            )
        )

        return metrics
