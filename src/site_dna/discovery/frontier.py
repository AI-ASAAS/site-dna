"""Intelligent URL frontier prioritizing key pages with bilingual scoring and depth bounding."""

import heapq
from typing import Optional
from urllib.parse import urlsplit

from site_dna.discovery.url_validator import is_same_origin, normalize_url

# Keywords for prioritizing strategic pages (English and Arabic)
PRIORITY_KEYWORDS: dict[str, tuple[list[str], int]] = {
    "contact": (["contact", "contact-us", "contactus", "اتصل", "تواصل", "اتصل-بنا", "اتصل_بنا"], 90),
    "about": (["about", "about-us", "aboutus", "company", "من-نحن", "من_نحن", "عنا", "عن-الشركة"], 85),
    "services": (["service", "services", "خدمات", "خدماتنا"], 80),
    "products": (["product", "products", "solutions", "منتجات", "منتجاتنا", "حلول", "حلولنا"], 75),
    "pricing": (["price", "pricing", "plans", "أسعار", "الاسعار", "خطط", "باقات"], 70),
    "portfolio": (["portfolio", "projects", "case-studies", "clients", "أعمالنا", "مشاريع", "عملاؤنا"], 65),
    "blog": (["blog", "news", "articles", "مدونة", "أخبار", "مقالات"], 50),
    "faq": (["faq", "frequently-asked-questions", "أسئلة", "الأسئلة-الشائعة"], 45),
}


def calculate_url_priority(url: str, depth: int, anchor_text: str = "") -> int:
    """Calculate priority score for an internal candidate URL.

    Scores range from 0 to 100:
    - Root / Home: 100
    - Strategic pages (Contact, About, Services, etc.): 45 - 90
    - General pages: 25 - (depth * 5)
    """
    parts = urlsplit(url)
    path = parts.path.strip("/")
    combined_signal = f"{path.lower()} {anchor_text.lower()} {parts.query.lower()}"

    # Seed / Root page
    if not path or path in ("", "index.html", "index.php", "home"):
        if depth == 0:
            return 100
        return 95

    # Match strategic categories
    for _, (keywords, score) in PRIORITY_KEYWORDS.items():
        if any(kw in combined_signal for kw in keywords):
            return score

    # General page: base score penalized by depth
    base_score = 25 - (depth * 5)
    return max(5, base_score)


class FrontierItem:
    """An enqueued URL candidate."""

    def __init__(self, url: str, depth: int, priority: int, anchor_text: str = ""):
        self.url = url
        self.depth = depth
        self.priority = priority
        self.anchor_text = anchor_text


class IntelligentFrontier:
    """Thread-safe-compatible priority queue managing crawl candidates."""

    def __init__(
        self,
        canonical_origin: str,
        max_depth: int = 2,
        max_candidates: int = 200,
    ):
        self.canonical_origin = canonical_origin
        self.max_depth = max_depth
        self.max_candidates = max_candidates

        # Priority heap: elements are (-priority, depth, sequence, FrontierItem)
        self._heap: list[tuple[int, int, int, FrontierItem]] = []
        self._counter: int = 0
        self._seen_urls: set[str] = set()
        self._visited_urls: set[str] = set()
        self._discovered_internal_links: set[str] = set()

    def add_candidate(self, url: str, depth: int, anchor_text: str = "") -> bool:
        """Validate, score, and enqueue a candidate URL if within budget and scope.

        Returns:
            True if enqueued, False if ignored (already seen, out of scope, depth exceeded).
        """
        if depth > self.max_depth:
            return False

        try:
            normalized = normalize_url(url)
        except Exception:
            return False

        # Only crawl URLs from the same origin
        if not is_same_origin(self.canonical_origin, normalized):
            return False

        self._discovered_internal_links.add(normalized)

        if normalized in self._seen_urls:
            return False

        if len(self._seen_urls) >= self.max_candidates:
            return False

        self._seen_urls.add(normalized)
        priority = calculate_url_priority(normalized, depth=depth, anchor_text=anchor_text)

        self._counter += 1
        item = FrontierItem(url=normalized, depth=depth, priority=priority, anchor_text=anchor_text)
        # Min-heap in Python: use -priority so highest priority items are popped first
        heapq.heappush(self._heap, (-priority, depth, self._counter, item))
        return True

    def pop_next(self) -> Optional[FrontierItem]:
        """Pop the next highest priority unvisited candidate from the frontier."""
        while self._heap:
            _, _, _, item = heapq.heappop(self._heap)
            if item.url not in self._visited_urls:
                return item
        return None

    def mark_visited(self, url: str):
        """Mark a URL as completed."""
        try:
            norm = normalize_url(url)
            self._visited_urls.add(norm)
        except Exception:
            self._visited_urls.add(url)

    def is_visited(self, url: str) -> bool:
        """Check if a URL was already crawled."""
        try:
            norm = normalize_url(url)
            return norm in self._visited_urls
        except Exception:
            return url in self._visited_urls

    def has_candidates(self) -> bool:
        """Check if unvisited candidates remain in the queue."""
        return any(item[3].url not in self._visited_urls for item in self._heap)

    def get_discovered_urls(self) -> list[str]:
        """Retrieve all unique internal URLs discovered during crawl."""
        return sorted(self._discovered_internal_links)

    @property
    def queue_size(self) -> int:
        return len(self._heap)
