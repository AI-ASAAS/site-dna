"""Technical SEO scoring engine implementing the 6-dimension weighted rubric."""

from typing import Optional

from site_dna.schemas.technical_seo import (
    TechnicalPageRecord,
    TechnicalSEOFinding,
    TechnicalSEOScore,
)


class TechnicalSEOScoringEngine:
    """Computes explainable, evidence-backed scores across the 6 Technical SEO dimensions."""

    DIMENSIONS: list[tuple[str, str, float]] = [
        ("crawlability", "إمكانية الزحف والاكتشاف الداخلي (Crawlability & Internal Discovery)", 0.20),
        ("indexability", "إشارات الفهرسة والروابط المعيارية (Indexability & Canonical Signals)", 0.20),
        ("metadata", "البيانات الوصفية للرأس (Technical Metadata)", 0.15),
        ("structured_data", "البيانات المنظمة والمخططات (Structured Data)", 0.10),
        ("mobile_js_seo", "SEO الجوال وتصيير جافاسكربت (Mobile & JavaScript SEO)", 0.15),
        ("performance", "الأداء وسرعة التحميل (Performance & Core Web Vitals)", 0.20),
    ]

    SEVERITY_DEDUCTIONS: dict[str, float] = {
        "critical": 25.0,
        "high": 15.0,
        "medium": 8.0,
        "low": 3.0,
        "info": 0.0,
    }

    @classmethod
    def calculate_scores(
        cls,
        pages: list[TechnicalPageRecord],
        findings: list[TechnicalSEOFinding],
        performance_measured: bool = True,
    ) -> tuple[Optional[float], list[TechnicalSEOScore]]:
        """Calculate weighted dimension scores and explainable overall score."""
        scores: list[TechnicalSEOScore] = []
        if not pages:
            return None, scores

        # Map findings by dimension category
        findings_by_dim: dict[str, list[TechnicalSEOFinding]] = {dim[0]: [] for dim in cls.DIMENSIONS}

        for f in findings:
            cat = f.category
            if cat in ("crawlability", "sitemap", "redirects", "internal_links"):
                findings_by_dim["crawlability"].append(f)
            elif cat in ("indexability", "canonical"):
                findings_by_dim["indexability"].append(f)
            elif cat == "metadata":
                findings_by_dim["metadata"].append(f)
            elif cat == "structured_data":
                findings_by_dim["structured_data"].append(f)
            elif cat in ("javascript_seo", "mobile_seo", "international_seo"):
                findings_by_dim["mobile_js_seo"].append(f)
            elif cat in ("performance", "core_web_vitals"):
                findings_by_dim["performance"].append(f)

        # Check structured data presence across pages
        has_schema = any(p.structured_data for p in pages)

        total_weighted_score = 0.0
        total_active_weight = 0.0

        for dim_key, dim_name_ar, weight in cls.DIMENSIONS:
            # Neutral handling for structured data if site is simple documentation/example
            if dim_key == "structured_data" and not has_schema and len(pages) <= 2:
                scores.append(
                    TechnicalSEOScore(
                        dimension_name=dim_key,
                        dimension_name_ar=dim_name_ar,
                        weight=weight,
                        score=100.0,
                        status="neutral",
                        rationale="لم يتم رصد بيانات منظمة في هذا النطاق المحدود (تقييم محايد).",
                        evidence_count=0,
                    )
                )
                total_weighted_score += 100.0 * weight
                total_active_weight += weight
                continue

            dim_findings = findings_by_dim.get(dim_key, [])
            deductions = sum(cls.SEVERITY_DEDUCTIONS.get(f.severity, 5.0) for f in dim_findings)
            raw_score = max(0.0, min(100.0, 100.0 - deductions))

            rationale = (
                f"احتُسبت الدرجة ({raw_score:.1f}/100) استناداً إلى {len(dim_findings)} ملاحظة موثقة بالأدلة."
                if dim_findings
                else f"درجة كاملة ({raw_score:.1f}/100) لخلو البعد من أي مشكلات تقنية موثقة."
            )

            scores.append(
                TechnicalSEOScore(
                    dimension_name=dim_key,
                    dimension_name_ar=dim_name_ar,
                    weight=weight,
                    score=raw_score,
                    status="assessed",
                    rationale=rationale,
                    evidence_count=len(dim_findings),
                )
            )

            total_weighted_score += raw_score * weight
            total_active_weight += weight

        overall_score: Optional[float] = None
        if total_active_weight >= 0.60:
            overall_score = round(total_weighted_score / total_active_weight, 1)

        return overall_score, scores
