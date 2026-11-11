"""Canonical FinalReportContext builder assembling data across all Site DNA analysis phases."""

from pathlib import Path
from typing import Any, Optional

from site_dna.core.logging import get_logger
from site_dna.reporting.evidence_catalog import EvidenceCatalogBuilder
from site_dna.reporting.source_adapters import SourceArtifactsAdapter
from site_dna.schemas.final_report import (
    FinalReportContext,
    ReportFindingItem,
    ReportPaperSize,
    ReportProvenance,
    ReportRecommendationItem,
    ReportStatus,
)

logger = get_logger("reporting.context_builder")

_ALL_STANDARD_STAGES = [
    "discovery",
    "visual_capture",
    "visual_identity",
    "ux_ui",
    "content_marketing",
    "technical_seo",
    "competitor_intelligence",
    "security_privacy",
    "accessibility",
    "strategic_intelligence",
]


class ReportContextBuilder:
    """Builds the canonical report context for final report generation and PDF export."""

    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.crawl_run_id = run_dir.name
        self.adapter = SourceArtifactsAdapter(run_dir)

    def build_context(
        self,
        mode: Any = "comprehensive",
        language: str = "ar",
        paper_size: ReportPaperSize = "A4",
        target_agent: Optional[str] = None,
        **kwargs: Any,
    ) -> FinalReportContext:
        """Assemble all available phase artifacts into a consolidated FinalReportContext."""
        if hasattr(mode, "mode"):
            req = mode
            mode = getattr(req, "mode", "comprehensive")
            language = getattr(req, "language", language)
            paper_size = getattr(req, "paper_size", paper_size)
            target_agent = getattr(req, "target_agent", target_agent)
        # 1. Discovery information
        cdata, cprov = self.adapter.get_discovery_info()
        target_url = cdata.get("website_info", {}).get("initial_url", "https://unknown-target.example.com")

        # 2. Evidence Catalog
        catalog_builder = EvidenceCatalogBuilder(self.run_dir, target_url)
        evidence_catalog = catalog_builder.build_catalog()

        # 3. Visual Capture
        _, vprov, screenshots_b64 = self.adapter.get_visual_capture_data()

        # 4. Ingest each specialized phase
        all_findings: list[ReportFindingItem] = []
        all_recs: list[ReportRecommendationItem] = []
        all_provenance: list[ReportProvenance] = []
        scores: dict[str, float] = {}

        if cprov:
            all_provenance.append(cprov)
        if vprov:
            all_provenance.append(vprov)

        # Stage mappings
        stage_configs = [
            ("visual_identity", "analysis/visual-identity", "visual_identity_agent"),
            ("ux_ui", "analysis/ux-ui", "ux_ui_agent"),
            ("content_marketing", "analysis/content-marketing", "content_marketing_agent"),
            ("technical_seo", "analysis/technical-seo", "technical_seo_agent"),
            ("competitor_intelligence", "analysis/competitors", "competitor_intelligence_agent"),
            ("security_privacy", "analysis/security-privacy", "security_privacy_agent"),
            ("accessibility", "analysis/accessibility", "accessibility_agent"),
        ]

        for st_id, subpath, ag_id in stage_configs:
            f_list, r_list, sc, prov = self.adapter.extract_stage_findings_and_recs(st_id, subpath, ag_id)
            if prov:
                all_provenance.append(prov)
                if sc is not None:
                    scores[st_id] = float(sc)
                all_findings.extend(f_list)
                all_recs.extend(r_list)

        # 5. Ingest Strategic Intelligence (Phase 11)
        strat_findings, strat_actions, waves, strat_idx, strat_label, strat_prov, strat_raw = (
            self.adapter.get_strategic_intelligence_data()
        )
        if strat_prov:
            all_provenance.append(strat_prov)
            if strat_idx is not None:
                scores["strategic_intelligence"] = float(strat_idx)

        # Determine which findings to display: prefer unified findings if available, else all raw
        display_findings = strat_findings if strat_findings else all_findings
        display_recs = strat_actions if strat_actions else all_recs

        # Identify critical issues (P0 or Critical)
        critical_issues = [
            f for f in display_findings if f.severity in ("critical", "high")
        ]

        # Calculate coverage
        executed_stages = {p.stage_id for p in all_provenance}
        missing_stages = [st for st in _ALL_STANDARD_STAGES if st not in executed_stages]

        # Status determination
        if not missing_stages:
            status: ReportStatus = "completed"
        elif len(executed_stages) >= 3:
            status = "partial"
        else:
            status = "source_missing"

        # Explicit limitations list
        limitations = [
            "التقرير مبني بشكل كامل وحصري على الأدلة التقنية المرصودة أثناء جولة الفحص المؤتمتة.",
            "لا يقدم التقرير أي ضمانات مالية أو نسب نمو استثماري أو افتراضات غير مثبتة.",
            "الفحوصات الأمنية سلبية ودفاعية ولا تمثل تقييم اختراق كامل للأنظمة الخلفية (Pentest).",
            "نتائج إمكانية الوصول تغطي معايير WCAG 2.2 القابلة للأتمتة وتتطلب مراجعة بشرية للتقييم النهائي.",
        ]
        if missing_stages:
            limitations.append(
                f"المراحل التالية لم تكتمل في هذه الجولة وتم توثيق غيابها بأمانة: {', '.join(missing_stages)}."
            )

        # Summary narrative
        exec_md = strat_raw.get("executive_summary_md", "")
        if not exec_md:
            exec_md = (
                f"يقدم هذا التقرير تحليلاً استراتيجياً وتقنياً موحداً لموقع {target_url}. "
                f"تم فحص وتقييم {len(executed_stages)} محاور تقنية بنجاح ورصد {len(display_findings)} ملاحظة موحدة "
                f"مع تحديد {len(critical_issues)} مشكلة حرجة تتطلب تدخلاً سريعاً، "
                f"وبناء خارطة طريق علاجية تتضمن {len(display_recs)} مهمة موزعة على 4 موجات تنفيذية."
            )

        exec_ar = exec_md

        key_conclusions = [
            f"إجمالي المحاور المفحوصة والموثقة: {len(executed_stages)} محاور تقنية.",
            f"إجمالي الملاحظات المرصودة بعد إلغاء التكرار: {len(display_findings)} ملاحظة.",
            f"المشاكل ذات الأولوية القصوى (P0/Critical): {len(critical_issues)} تتطلب المعالجة الفورية.",
            f"خطة العمل التنفيذية: تتألف من {len(display_recs)} إجراءً علاجياً مرتباً بأولويات محكمة.",
        ]

        # Filter if single-agent mode requested
        if mode == "agent" and target_agent:
            display_findings = [f for f in display_findings if f.source_agent == target_agent or f.domain == target_agent]
            display_recs = [r for r in display_recs if r.owner_role.lower() == target_agent.lower()]

        # 6. Deep domain audits
        domain_audits = self.adapter.get_domain_audits()

        return FinalReportContext(
            target_url=target_url,
            crawl_run_id=self.crawl_run_id,
            mode=mode,
            language=language if language in ("ar", "en") else "ar",
            paper_size=paper_size,
            status=status,
            executive_summary_md=exec_md,
            executive_summary_ar=exec_ar,
            key_conclusions=key_conclusions,
            coverage={
                "available_stages": list(executed_stages),
                "missing_stages": missing_stages,
                "coverage_ratio": round(len(executed_stages) / len(_ALL_STANDARD_STAGES), 2),
            },
            scores=scores,
            strategic_index=strat_idx,
            strategic_label_ar=strat_label or "تقييم جاهزية تقنية",
            findings=display_findings,
            critical_issues=critical_issues,
            recommendations=display_recs,
            roadmap_waves=waves,
            evidence_catalog=evidence_catalog,
            source_manifest=all_provenance,
            limitations=limitations,
            missing_stages=missing_stages,
            desktop_screenshot_b64=screenshots_b64.get("desktop"),
            mobile_screenshot_b64=screenshots_b64.get("mobile"),
            domain_audits=domain_audits,
        )
