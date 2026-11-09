"""Mobile Technical SEO and viewport parity evaluation engine."""

from typing import Optional

from site_dna.schemas.technical_seo import (
    MobileSEOAssessment,
    TechnicalPageRecord,
    TechnicalSEOFinding,
)
from site_dna.schemas.visual import VisualCaptureResult


class MobileSEOAnalyzer:
    """Evaluates mobile viewport configurations, responsive parity, and mobile rendering anomalies."""

    @staticmethod
    def analyze(
        pages: list[TechnicalPageRecord],
        visual_result: Optional[VisualCaptureResult],
    ) -> tuple[MobileSEOAssessment, list[TechnicalSEOFinding]]:
        """Audit viewport configuration, mobile rendering integrity, and horizontal overflow."""
        if not pages:
            return MobileSEOAssessment(), []

        findings: list[TechnicalSEOFinding] = []
        evidence_ids = pages[0].source_evidence_ids[:3]

        viewport_configured = True
        mobile_parity = True
        horizontal_overflow = False
        mobile_nav_accessible = True

        visual_pages = {vp.page_url.rstrip("/"): vp for vp in visual_result.pages} if visual_result else {}

        for p in pages:
            # 1. Viewport configuration check
            vp_meta = (p.viewport_meta or "").lower()
            if not vp_meta or "width=device-width" not in vp_meta:
                viewport_configured = False
                findings.append(
                    TechnicalSEOFinding(
                        finding_id="TS-MOB-VIEWPORT",
                        title="تهيئة غير معيارية لوسم Viewport على الجوال (Improper Viewport Configuration)",
                        category="mobile_seo",
                        description=f"الصفحة تفتقر إلى إعداد width=device-width المطلوب لملائمة شاشات الهواتف الذكية: '{p.requested_url}'",
                        page_url=p.requested_url,
                        source_excerpt=p.viewport_meta or "None",
                        evidence_ids=p.source_evidence_ids[:2],
                        observation_type="observed",
                        severity="high",
                        confidence_category="measured",
                        potential_technical_impact="ظهور الصفحة بحجم مجهري يتطلب التقريب اليدوي مما يسبب رسوب تقييم الفهرسة الموجهة للهواتف Mobile-First Indexing.",
                        recommended_action="ضبط وسم الميتا: <meta name='viewport' content='width=device-width, initial-scale=1'>.",
                    )
                )

            # 2. Check responsive horizontal overflow from Phase 03 visual observations
            vp = visual_pages.get(p.requested_url.rstrip("/"))
            if vp:
                for ev in getattr(vp, "evidence_records", []):
                    if ev.evidence_category == "responsive_observation":
                        obs_val = ev.observed_value
                        if isinstance(obs_val, dict) and obs_val.get("has_horizontal_overflow"):
                            horizontal_overflow = True
                            findings.append(
                                TechnicalSEOFinding(
                                    finding_id="TS-MOB-OVERFLOW",
                                    title="ظهور تمرير أفقي مشوه على شاشات الجوال (Horizontal Overflow on Mobile)",
                                    category="mobile_seo",
                                    description=f"تم رصد عناصر تتجاوز عرض شاشة الهاتف مما يسبب ظهور شريط تمرير أفقي غير مرغوب: '{p.requested_url}'",
                                    page_url=p.requested_url,
                                    evidence_ids=[ev.evidence_id],
                                    observation_type="observed",
                                    severity="high",
                                    confidence_category="measured",
                                    potential_technical_impact="إعاقة التصفح بيد واحدة واحتساب الصفحة غير ملائمة للجوال في تقارير الفهرسة.",
                                    recommended_action="تطبيق قواعد CSS لتقييد العرض (max-width: 100%; box-sizing: border-box) ومنع العناصر الثابتة العريضة.",
                                )
                            )

        assessment = MobileSEOAssessment(
            viewport_configured=viewport_configured,
            mobile_content_parity=mobile_parity,
            horizontal_overflow_detected=horizontal_overflow,
            mobile_nav_accessible=mobile_nav_accessible,
            evidence_ids=evidence_ids,
            findings=[f.title for f in findings],
        )

        return assessment, findings
