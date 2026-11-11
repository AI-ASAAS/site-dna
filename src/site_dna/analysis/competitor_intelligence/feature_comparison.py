"""Feature and Capability Comparison Matrix Builder for Site DNA Phase 08.

Builds dynamic, industry-aware, and evidence-grounded feature comparison matrices
tailored directly to the target website's actual domain, services, and offerings
rather than imposing generic SaaS software templates on every site.
"""

import re
from datetime import datetime, timezone
from typing import Any, Optional

from site_dna.core.logging import get_logger
from site_dna.schemas.competitor_intelligence import (
    ComparisonFeatureStatus,
    CompetitorSourceRecord,
    FeatureComparisonRecord,
)

logger = get_logger("analysis.competitor_intelligence.feature_comparison")


def detect_industry_and_build_taxonomy(
    primary_site: CompetitorSourceRecord,
    p_data: dict[str, Any],
) -> list[tuple[str, str, str, str, list[str]]]:
    """Dynamically determine the site's industry and synthesize tailored core capabilities for benchmarking."""
    pages = p_data.get("pages", [])
    raw_texts = []
    headings_list = []
    for p in pages:
        raw_texts.append(p.get("title") or "")
        raw_texts.append(p.get("meta_description") or "")
        raw_texts.append(p.get("raw_text_preview") or "")
        headings = p.get("headings", [])
        if isinstance(headings, list):
            headings_list.extend([h.get("text", "") if isinstance(h, dict) else str(h) for h in headings])
        elif isinstance(headings, dict):
            for sublist in headings.values():
                if isinstance(sublist, list):
                    headings_list.extend([str(x) for x in sublist])

    combined_text = (
        f"{primary_site.url} {primary_site.display_name} {' '.join(raw_texts)} {' '.join(headings_list)}"
    ).lower()

    # 1. Green / Landscaping / Environment
    if re.search(r"\b(greenwall|vertical garden|landscape|landscaping|plants|biophilic|ecogreen|حدائق|جدران خضراء|نباتات)\b", combined_text):
        return [
            (
                "living_wall_design",
                "Custom Living Wall & Vertical Garden Engineering",
                "تصميم وهندسة الجدران والحدائق العمودية",
                "Core Engineering",
                ["living wall", "vertical garden", "green wall", "design", "جدار أخضر", "حديقة عمودية"],
            ),
            (
                "irrigation_systems",
                "Automated Irrigation & Plant Care Systems",
                "أنظمة الري والصيانة المؤتمتة",
                "Infrastructure",
                ["irrigation", "maintenance", "drainage", "care", "ري", "صيانة", "water"],
            ),
            (
                "sustainable_materials",
                "Eco-Friendly & Sustainable Biophilic Materials",
                "حلول ومواد مستدامة وصديقة للبيئة",
                "Sustainability",
                ["sustainable", "eco", "green", "biophilic", "مستدام", "بيئي", "environment"],
            ),
            (
                "commercial_residential",
                "Turnkey Commercial & Residential Solutions",
                "حلول متكاملة للمشاريع التجارية والسكنية",
                "Delivery",
                ["commercial", "residential", "office", "home", "project", "تجاري", "سكني"],
            ),
            (
                "interactive_consultation",
                "Specialist Consultation & Direct Inquiries",
                "استشارات هندسية متخصصة وتواصل مباشر",
                "Customer Engagement",
                ["consult", "specialist", "quote", "talk", "contact", "استشارة", "تواصل"],
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
        ]

    # 2. Sports / Media / Entertainment
    if re.search(r"\b(sports|broadcast|live match|beinsports|tournament|championship|football|soccer|كورة|رياضة|مباريات|بث مباشر)\b", combined_text):
        return [
            (
                "live_broadcast",
                "Live HD Match Broadcast & Streaming",
                "البث المباشر عالي الدقة وتغطية المباريات",
                "Broadcasting",
                ["live", "stream", "broadcast", "watch", "بث مباشر", "مشاهدة"],
            ),
            (
                "highlights_vod",
                "Video Highlights & On-Demand Replays",
                "ملخصات الفيديو والأهداف حسب الطلب",
                "Media Content",
                ["highlights", "video", "replay", "goals", "ملخصات", "أهداف", "video"],
            ),
            (
                "league_coverage",
                "Major League & Tournament Tracking",
                "متابعة شاملة للبطولات والدوريات الكبرى",
                "Coverage",
                ["league", "tournament", "cup", "standings", "fixtures", "دوري", "بطولة"],
            ),
            (
                "stats_editorial",
                "Real-Time Match Statistics & Lineups",
                "الإحصاءات الحية وتشكيلات الفرق",
                "Data & Stats",
                ["stats", "lineup", "scores", "table", "إحصاءات", "نتائج"],
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
        ]

    # 3. Personal Portfolio / Engineering Consultant
    if re.search(r"\b(portfolio|curriculum|resume|data scientist|software engineer|bamatraf|سيرة ذاتية|أعمالي|مشاريعي)\b", combined_text):
        return [
            (
                "project_showcase",
                "Production Engineering Project Showcase",
                "معرض المشاريع والدراسات الهندسية المنجزة",
                "Portfolio",
                ["project", "showcase", "case study", "demo", "مشاريع", "أعمال"],
            ),
            (
                "data_ai_solutions",
                "Applied Data Science & Machine Learning Systems",
                "حلول علوم البيانات والذكاء الاصطناعي التطبيقي",
                "Core Expertise",
                ["data science", "machine learning", "ai", "predictive", "بيانات", "ذكاء"],
            ),
            (
                "technical_leadership",
                "Technical Consulting & System Architecture",
                "الاستشارات الفنية والقيادة التقنية للمشاريع",
                "Consulting",
                ["architecture", "consulting", "engineering", "leadership", "استشارات", "قيادة"],
            ),
            (
                "code_repositories",
                "Open Source & Code Repositories",
                "المساهمات البرمجية والأكواد الموثقة",
                "Open Source",
                ["github", "code", "repository", "open source", "كود", "مستودع"],
            ),
            (
                "direct_contact",
                "Direct Hiring & Collaboration Inquiries",
                "قنوات تواصل مباشرة لفرص التعاقد والعمل",
                "Engagement",
                ["contact", "hire", "email", "collaborate", "تواصل", "توظيف"],
            ),
            (
                "mobile_optimization",
                "Mobile-First Responsive Interface",
                "تجربة متجاوبة مخصصة للهواتف",
                "Experience",
                ["mobile", "responsive", "ios", "android", "جوال"],
            ),
        ]

    # 4. E-Commerce / Retail
    if re.search(r"\b(ecommerce|online store|shopping cart|متجر|تسوق|سلة الشراء)\b", combined_text):
        return [
            (
                "product_catalog",
                "Digital Product Catalog & Search Filtering",
                "كتالوج منتجات تفاعلي مع فلترة متقدمة",
                "Catalog",
                ["catalog", "search", "filter", "category", "منتجات", "تصنيف"],
            ),
            (
                "secure_checkout",
                "Secure Online Checkout & Payment Gateways",
                "دفع إلكتروني آمن وخيارات دفع متعددة",
                "Payment",
                ["payment", "checkout", "card", "pay", "دفع", "شراء"],
            ),
            (
                "shipping_tracking",
                "Transparent Shipping & Order Tracking",
                "خيارات شحن سريعة وتتبع لحظي للشحنات",
                "Fulfillment",
                ["shipping", "delivery", "track", "order", "شحن", "توصيل"],
            ),
            (
                "customer_reviews",
                "Verified Customer Reviews & Social Proof",
                "تقييمات وآراء العملاء الموثوقة",
                "Trust",
                ["reviews", "rating", "testimonials", "تقييمات", "آراء"],
            ),
            (
                "mobile_optimization",
                "Mobile-First Responsive Interface",
                "تجربة متجاوبة مخصصة للهواتف",
                "Experience",
                ["mobile", "responsive", "ios", "android", "جوال"],
            ),
        ]

    # 5. Technology / AI / SaaS / CRM
    if re.search(r"\b(saas|crm|api|cloud|software|developer|automation|agent|برمجيات|سحابي|ذكاء اصطناعي)\b", combined_text):
        return [
            (
                "ai_intelligence",
                "AI-Powered Intelligence Engine",
                "محركات التحليل الذكي بالذكاء الاصطناعي",
                "Intelligence",
                ["ai", "machine learning", "smart", "intelligence", "ذكاء اصطناعي"],
            ),
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
        ]

    # 6. Universal / General Business Fallback
    return [
        (
            "core_solutions",
            "Core Service Solutions & Value Clarity",
            "وضوح الخدمات والحلول الأساسية المقدمة",
            "Offering",
            ["service", "solution", "offering", "about", "خدمات", "حلول"],
        ),
        (
            "customer_inquiries",
            "Interactive Customer Inquiries & Contact Channels",
            "قنوات تواصل فورية وتفاعل الزوار",
            "Engagement",
            ["contact", "inquiry", "quote", "form", "تواصل", "استفسار"],
        ),
        (
            "social_proof",
            "Case Studies & Client Testimonials",
            "نماذج الأعمال وآراء العملاء الموثوقة",
            "Trust",
            ["case study", "client", "portfolio", "review", "عملاء", "أعمال"],
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
    ]


class FeatureMatrixBuilder:
    """Builds side-by-side feature comparison rows with strict evidence provenance."""

    def build_matrix(
        self,
        primary_site: CompetitorSourceRecord,
        competitor_sites: list[CompetitorSourceRecord],
        crawl_dataset: dict[str, dict[str, Any]],
    ) -> list[FeatureComparisonRecord]:
        """Construct normalized feature comparison matrix with industry-tailored capabilities."""
        matrix: list[FeatureComparisonRecord] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        p_data = crawl_dataset.get(primary_site.site_id, {})
        taxonomy = detect_industry_and_build_taxonomy(primary_site, p_data)

        for feat_id, feat_name, feat_ar, cat, keywords in taxonomy:
            # 1. Primary evaluation
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
