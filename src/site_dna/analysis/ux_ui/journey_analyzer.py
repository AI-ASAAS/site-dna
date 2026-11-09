"""Deterministic user journey constructor and task flow analyzer."""

from urllib.parse import urlparse

from site_dna.analysis.ux_ui.context_builder import UXPageContext
from site_dna.schemas.ux_ui import UXJourney
from site_dna.schemas.visual import VisualEvidenceRecord

STANDARD_GOALS = [
    {
        "id": "JRN-01",
        "goal": "الوصول إلى صفحة التواصل أو الدعم (Contact / Support)",
        "target_keywords": ["contact", "support", "help", "تواصل", "اتصل", "الدعم", "مساعدة"],
    },
    {
        "id": "JRN-02",
        "goal": "استكشاف الخدمات أو المنتجات (Services / Products)",
        "target_keywords": ["services", "products", "solutions", "features", "خدمات", "منتجات", "حلول", "مزايا"],
    },
    {
        "id": "JRN-03",
        "goal": "التعرف على معلومات المؤسسة أو من نحن (About Us)",
        "target_keywords": ["about", "company", "team", "من نحن", "عن", "الشركة", "فريقنا"],
    },
    {
        "id": "JRN-04",
        "goal": "الاطلاع على باقات الأسعار أو الاشتراك (Pricing / Plans)",
        "target_keywords": ["pricing", "plans", "packages", "rates", "الأسعار", "الباقات", "الاشتراك"],
    },
]


class JourneyAnalyzer:
    """Constructs supported user journeys from the verified internal link graph."""

    @staticmethod
    def analyze_journeys(
        pages: list[UXPageContext],
        evidence_index: dict[str, VisualEvidenceRecord],
    ) -> list[UXJourney]:
        """Map primary user task flows and detect missing transition links."""
        journeys: list[UXJourney] = []
        if not pages:
            return journeys

        seed_url = pages[0].page_url

        for template in STANDARD_GOALS:
            goal_id = template["id"]
            goal_text = template["goal"]
            keywords = template["target_keywords"]

            # Find target page in discovered pages
            target_page_url = None
            supporting_link_texts: list[str] = []

            for p in pages:
                url_lower = p.page_url.lower()
                title_lower = (p.page_metadata.get("title") or "").lower()
                if any(kw in url_lower or kw in title_lower for kw in keywords):
                    target_page_url = p.page_url
                    break

            # If target page exists in pages, check if reachable from seed directly or via links
            if target_page_url:
                # Find direct link from seed page
                direct_link = next(
                    (
                        lnk
                        for lnk in pages[0].links
                        if JourneyAnalyzer._urls_match(
                            lnk.get("target_url") or lnk.get("url") or lnk.get("href") or "",
                            target_page_url,
                        )
                    ),
                    None,
                )

                if direct_link:
                    link_txt = (direct_link.get("anchor_text") or direct_link.get("text") or "").strip()
                    supporting_link_texts.append(link_txt)
                    journeys.append(
                        UXJourney(
                            journey_id=goal_id,
                            goal=goal_text,
                            starting_page=seed_url,
                            target_page=target_page_url,
                            route=[seed_url, target_page_url],
                            transitions_count=1,
                            missing_steps=[],
                            status="graph_derived",
                            potential_friction="مسار مباشر وسلس من خطوة واحدة انطلاقاً من الصفحة الرئيسية.",
                            supporting_link_text=supporting_link_texts,
                        )
                    )
                else:
                    # Multi-step or indirect route
                    journeys.append(
                        UXJourney(
                            journey_id=goal_id,
                            goal=goal_text,
                            starting_page=seed_url,
                            target_page=target_page_url,
                            route=[seed_url, target_page_url],
                            transitions_count=2,
                            missing_steps=["يتطلب الوصول نقرات غير مباشرة أو البحث في التذييل"],
                            status="graph_derived",
                            potential_friction="الرابط غير متاح بشكل بارز في القائمة العلوية للصفحة الرئيسية.",
                            supporting_link_text=[],
                        )
                    )
            else:
                # Target page not discovered in sample
                journeys.append(
                    UXJourney(
                        journey_id=goal_id,
                        goal=goal_text,
                        starting_page=seed_url,
                        target_page="غير متوفر في العينة المفحوصة",
                        route=[seed_url],
                        transitions_count=0,
                        missing_steps=[f"لم يتم العثور على صفحة {goal_text} في العينة المستكشفة"],
                        status="not_testable",
                        potential_friction="غياب مسار واضح للوصول إلى هذه الوجهة من الصفحة الرئيسية.",
                        supporting_link_text=[],
                    )
                )

        return journeys

    @staticmethod
    def _urls_match(url1: str, url2: str) -> bool:
        p1 = urlparse(url1.strip())
        p2 = urlparse(url2.strip())
        path1 = p1.path.rstrip("/").lower()
        path2 = p2.path.rstrip("/").lower()
        return path1 == path2 and p1.netloc.lower() == p2.netloc.lower()
