"""Feature and Capability Comparison Matrix Builder for Site DNA Phase 08."""

from datetime import datetime, timezone
from typing import Any, Optional

from site_dna.core.logging import get_logger
from site_dna.schemas.competitor_intelligence import (
    ComparisonFeatureStatus,
    CompetitorSourceRecord,
    FeatureComparisonRecord,
)

logger = get_logger("analysis.competitor_intelligence.feature_comparison")

CORE_FEATURES_TAXONOMY = [
    (
        "api_access",
        "API & Developer Platform",
        "منصة وواجهات برمجة التطبيقات (API)",
        "Architecture",
        ["api", "developer", "webhook", "endpoints", "sdk"],
    ),
    (
        "realtime_monitoring",
        "Real-Time Telemetry & Monitoring",
        "المراقبة اللحظية والتحليلات الحية",
        "Analytics",
        ["realtime", "real-time", "live", "telemetry", "monitor", "dashboard"],
    ),
    (
        "automated_reporting",
        "Automated Strategic Reporting",
        "إعداد التقارير الاستراتيجية الآلية",
        "Reporting",
        ["report", "export", "pdf", "audit", "summary", "تقرير"],
    ),
    (
        "ai_intelligence",
        "AI-Powered Intelligence Engine",
        "محركات التحليل الذكي بالذكاء الاصطناعي",
        "Intelligence",
        ["ai", "machine learning", "smart", "intelligence", "ذكاء اصطناعي"],
    ),
    (
        "enterprise_security",
        "Enterprise Security & Compliance",
        "الأمان المتقدم والامتثال المؤسسي",
        "Security",
        ["security", "soc2", "gdpr", "compliance", "sso", "rbac", "أمان"],
    ),
    (
        "mobile_optimization",
        "Mobile-First Responsive Interface",
        "تجربة متجاوبة مخصصة للهواتف",
        "Experience",
        ["mobile", "responsive", "ios", "android", "جوال"],
    ),
    (
        "bilingual_support",
        "Arabic & English Bilingual Support",
        "دعم كامل وثنائي للغتين العربية والإنجليزية",
        "Localization",
        ["arabic", "عربي", "bilingual", "rtl", "لغة"],
    ),
    (
        "self_serve_docs",
        "Public Documentation & Knowledgebase",
        "توثيق فني مفتوح وقاعدة معرفية",
        "Support",
        ["docs", "documentation", "guide", "knowledgebase", "توثيق"],
    ),
]


class FeatureMatrixBuilder:
    """Builds side-by-side feature comparison rows with strict evidence provenance."""

    def build_matrix(
        self,
        primary_site: CompetitorSourceRecord,
        competitor_sites: list[CompetitorSourceRecord],
        crawl_dataset: dict[str, dict[str, Any]],
    ) -> list[FeatureComparisonRecord]:
        """Construct normalized feature comparison matrix."""
        matrix: list[FeatureComparisonRecord] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        for feat_id, feat_name, feat_ar, cat, keywords in CORE_FEATURES_TAXONOMY:
            # 1. Primary evaluation
            p_data = crawl_dataset.get(primary_site.site_id, {})
            p_status, p_ev, p_expl = self._evaluate_site_feature(primary_site, p_data, keywords, feat_name)

            # 2. Competitors evaluation
            comp_statuses: dict[str, dict[str, Any]] = {}
            for comp in competitor_sites:
                c_data = crawl_dataset.get(comp.site_id, {})
                c_status, c_ev, c_expl = self._evaluate_site_feature(comp, c_data, keywords, feat_name)
                comp_statuses[comp.site_id] = {
                    "status": c_status,
                    "evidence_id": c_ev,
                    "explanation": c_expl,
                    "last_observed": now_iso,
                    "url": comp.url,
                }

            matrix.append(
                FeatureComparisonRecord(
                    feature_id=feat_id,
                    feature_name=feat_name,
                    feature_name_ar=feat_ar,
                    category=cat,
                    primary_status=p_status,
                    primary_evidence_id=p_ev,
                    primary_explanation=p_expl,
                    competitor_statuses=comp_statuses,
                    importance="core",
                )
            )

        return matrix

    def _evaluate_site_feature(
        self,
        site: CompetitorSourceRecord,
        data: dict[str, Any],
        keywords: list[str],
        feature_name: str,
    ) -> tuple[ComparisonFeatureStatus, Optional[str], str]:
        """Determine evidence status of feature on a specific site."""
        pages = data.get("pages", [])
        if not pages:
            return "not_assessed", None, "No collected pages available for inspection."

        full_text_lower = " ".join(
            [
                (p.get("title") or "")
                + " "
                + " ".join([h.get("text", "") for h in p.get("headings", []) if isinstance(h, dict)])
                for p in pages
            ]
        ).lower()

        matched_p = None
        matched_kw = None
        for p in pages:
            h_text = ""
            headings = p.get("headings", {})
            if isinstance(headings, dict):
                for h_list in headings.values():
                    if isinstance(h_list, list):
                        h_text += " " + " ".join(str(x) for x in h_list)
            elif isinstance(headings, list):
                h_text += " " + " ".join(h.get("text", str(h)) if isinstance(h, dict) else str(h) for h in headings)

            p_text = (
                (p.get("title") or "")
                + " "
                + (p.get("url") or "")
                + " "
                + (p.get("html") or "")
                + " "
                + (p.get("meta_description") or "")
                + " "
                + h_text
            ).lower()

            for kw in keywords:
                if kw in p_text:
                    matched_p = p
                    matched_kw = kw
                    break
            if matched_p:
                break

        if matched_p:
            ev_id = f"ev-{site.site_id}-feat-{matched_p.get('page_id', '0')}"
            return "observed_present", ev_id, f"Observed '{matched_kw}' reference on page {matched_p.get('url')}."

        # Check in overall body text
        if any(kw in full_text_lower for kw in keywords):
            ev_id = f"ev-{site.site_id}-claimed"
            return "claimed", ev_id, f"Mentioned in marketing copy on {site.display_name}."

        # Feature was not found in sample crawl — DO NOT claim company lacks it
        return (
            "not_found_in_sample",
            None,
            f"Not observed in the {len(pages)} collected pages of {site.display_name} (does not confirm absence in uncollected pages).",
        )
