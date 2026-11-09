"""Deterministic navigation and information architecture analyzer."""

from collections import deque
from typing import Any
from urllib.parse import urlparse

from site_dna.analysis.ux_ui.context_builder import UXPageContext
from site_dna.schemas.ux_ui import UXFinding, UXNavigationAssessment
from site_dna.schemas.visual import VisualEvidenceRecord

AMBIGUOUS_LABELS = {
    "click here",
    "here",
    "more",
    "read more",
    "learn more",
    "link",
    "details",
    "view",
    "اضغط هنا",
    "هنا",
    "المزيد",
    "اقرأ المزيد",
    "تفاصيل",
    "عرض",
    "رابط",
}


class NavigationAnalyzer:
    """Evaluates website navigation structure, link graph, labeling, and hierarchy."""

    @staticmethod
    def analyze_navigation(
        pages: list[UXPageContext],
        evidence_index: dict[str, VisualEvidenceRecord],
    ) -> UXNavigationAssessment:
        """Construct link graph and identify navigation anomalies and usability issues."""
        findings: list[UXFinding] = []
        graph_edges: list[dict[str, str]] = []
        links_count = 0
        unique_destinations: set[str] = set()

        all_page_urls = {p.page_url for p in pages}
        normalized_known_urls = {NavigationAnalyzer._normalize_url(p.page_url) for p in pages}
        adjacency: dict[str, set[str]] = {p.page_url: set() for p in pages}

        label_to_destinations: dict[str, set[str]] = {}
        ambiguous_instances: list[dict[str, Any]] = []
        duplicate_instances: list[dict[str, Any]] = []

        has_breadcrumbs_any = False
        has_footer_nav_any = False

        for page in pages:
            # 1. Check DOM elements for navigation landmarks
            page_nav_elements = [
                d
                for d in page.dom_elements
                if d.get("tag_name") in ("nav", "footer", "header")
                or "breadcrumb" in (d.get("class_name") or "").lower()
            ]

            for el in page_nav_elements:
                c_name = (el.get("class_name") or "").lower()
                tag = el.get("tag_name")
                if "breadcrumb" in c_name:
                    has_breadcrumbs_any = True
                if tag == "footer" or "footer" in c_name:
                    has_footer_nav_any = True

            # 2. Analyze links from crawl and DOM
            for link in page.links:
                target_url = link.get("target_url") or link.get("url") or link.get("href")
                if not target_url:
                    continue

                links_count += 1
                unique_destinations.add(target_url)

                text = (link.get("anchor_text") or link.get("text") or "").strip().lower()

                # Record graph edge if internal
                norm_target = NavigationAnalyzer._normalize_url(target_url)
                if norm_target in normalized_known_urls:
                    for known_url in all_page_urls:
                        if NavigationAnalyzer._normalize_url(known_url) == norm_target:
                            adjacency[page.page_url].add(known_url)
                            graph_edges.append({"source": page.page_url, "target": known_url})

                # Detect ambiguous link labels
                if text in AMBIGUOUS_LABELS:
                    ambiguous_instances.append(
                        {
                            "source_page": page.page_url,
                            "target_url": target_url,
                            "anchor_text": text,
                        }
                    )

                # Track duplicate labels pointing to different URLs
                if len(text) > 3 and not text.isdigit():
                    if text not in label_to_destinations:
                        label_to_destinations[text] = set()
                    label_to_destinations[text].add(target_url)

        # 3. Detect duplicate labels pointing to conflicting destinations
        for label, destinations in label_to_destinations.items():
            if len(destinations) > 1 and label not in AMBIGUOUS_LABELS:
                duplicate_instances.append({"label": label, "destinations": list(destinations)})

        # 4. Graph calculations: Shortest paths & reachability from seed (pages[0])
        seed_url = pages[0].page_url if pages else ""
        reachable_pages: set[str] = set()
        max_depth = 0

        if seed_url:
            queue: deque[tuple[str, int]] = deque([(seed_url, 0)])
            visited = {seed_url}

            while queue:
                curr_url, depth = queue.popleft()
                reachable_pages.add(curr_url)
                max_depth = max(max_depth, depth)

                for neighbor in adjacency.get(curr_url, set()):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, depth + 1))

        isolated_pages = [url for url in all_page_urls if url not in reachable_pages and url != seed_url]

        # 5. Generate structured findings
        if ambiguous_instances:
            first = ambiguous_instances[0]
            findings.append(
                UXFinding(
                    finding_id="UX-FIND-NAV-01",
                    title="استخدام نصوص روابط مبهمة وغير واضحة السياق",
                    category="navigation",
                    description=(
                        f"تم رصد {len(ambiguous_instances)} رابطاً بنصوص عامة مثل '{first['anchor_text']}' "
                        f"دون توضيح الوجهة المقصودة للمستخدم وقارئات الشاشة."
                    ),
                    source_page=first["source_page"],
                    viewport="desktop",
                    element_reference=f"a[href='{first['target_url']}']",
                    evidence_ids=[],
                    observation_type="observed",
                    severity="medium",
                    confidence_category="confirmed_by_measurement",
                    potential_user_impact="إرباك المستخدم وإضعاف القدرة على التنبؤ بمحتوى الصفحة التالية قبل النقر.",
                    recommended_action="استبدال العبارات المبهمة بنصوص وصفية واضحة تعكس المحتوى الهدف بدقة.",
                )
            )

        if duplicate_instances:
            first_dup = duplicate_instances[0]
            findings.append(
                UXFinding(
                    finding_id="UX-FIND-NAV-02",
                    title="تكرار نفس النص لروابط تشير إلى وجهات مختلفة",
                    category="information_architecture",
                    description=(
                        f"النص '{first_dup['label']}' يُستخدم للإشارة إلى عدة وجهات مختلفة "
                        f"({len(first_dup['destinations'])} وجهات)، مما يخل باتساق بنية التنقل."
                    ),
                    source_page=pages[0].page_url if pages else "",
                    viewport="desktop",
                    element_reference="nav a",
                    evidence_ids=[],
                    observation_type="derived",
                    severity="medium",
                    confidence_category="confirmed_by_measurement",
                    potential_user_impact="تشتيت المستخدم وتقليل الثقة في دلالة القوائم التوجيهية.",
                    recommended_action="توحيد التسميات أو تخصيص نصوص فريدة تعكس الوجهة المستقلة لكل رابط.",
                )
            )

        if isolated_pages and len(pages) > 2:
            findings.append(
                UXFinding(
                    finding_id="UX-FIND-NAV-03",
                    title="صفحات مستكشفة معزولة عن مسار التنقل الرئيسي",
                    category="navigation",
                    description=(
                        f"تم رصد {len(isolated_pages)} صفحة لا يمكن الوصول إليها عبر الروابط الداخلية "
                        f"انطلاقاً من الصفحة الرئيسية ضمن العينة المفحوصة."
                    ),
                    source_page=isolated_pages[0],
                    viewport="desktop",
                    evidence_ids=[],
                    observation_type="derived",
                    severity="low",
                    confidence_category="confirmed_by_measurement",
                    potential_user_impact="صعوبة عثور الزوار على هذه الصفحات الهامة دون كتابة الرابط المباشر.",
                    recommended_action="إدراج روابط واضحة لهذه الصفحات في القائمة الرئيسية أو التذييل.",
                )
            )

        return UXNavigationAssessment(
            links_count=links_count,
            unique_destinations_count=len(unique_destinations),
            reachable_pages=list(reachable_pages),
            isolated_pages=isolated_pages,
            max_navigation_depth=max_depth,
            has_breadcrumbs=has_breadcrumbs_any,
            has_footer_nav=has_footer_nav_any,
            ambiguous_labels=ambiguous_instances[:10],
            duplicate_labels=duplicate_instances[:10],
            graph_edges=graph_edges,
            findings=findings,
        )

    @staticmethod
    def _normalize_url(url: str) -> str:
        parsed = urlparse(url.strip())
        path = parsed.path.rstrip("/")
        return f"{parsed.netloc}{path}".lower()
