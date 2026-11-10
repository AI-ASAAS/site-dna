"""Table-driven, heuristic page categorizer (Phase 2).

Labels are intentionally simple and deterministic. They are documented as
`heuristic` evidence, not as ground truth.
"""

from urllib.parse import urlsplit

# Order matters: more specific labels are checked before broader ones.
CATEGORY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("contact", ("contact", "contact-us", "get-in-touch", "اتصل", "تواصل")),
    ("about", ("about", "about-us", "who-we-are", "company", "our-story", "من-نحن", "عنا")),
    ("pricing", ("pricing", "price", "plans", "packages", "rates", "أسعار", "باقات")),
    ("legal", ("terms", "privacy", "legal", "cookie", "refund", "imprint", "gdpr")),
    ("auth", ("login", "signin", "sign-in", "signup", "sign-up", "register", "auth", "password")),
    ("docs", ("docs", "documentation", "help", "faq", "guide", "support", "tutorial")),
    ("blog", ("blog", "news", "articles", "posts", "insights", "مدونة", "أخبار")),
    ("category", ("category", "categories", "collections", "catalog", "tag")),
    ("product", ("product", "products", "shop", "store", "item", "منتجات", "متجر")),
)


def categorize_url(url: str, depth: int = 0, title: str = "", h1: str = "") -> str:
    """Return one of: home, blog, product, category, contact, about, pricing,
    legal, auth, docs, other.

    The URL path is authoritative; title and H1 are used only when the path has
    no recognizable signal.
    """
    parts = urlsplit(url)
    path = parts.path.strip("/").lower()

    if depth == 0 or not path:
        return "home"

    path_signal = f"{path} {parts.query}".lower()
    for label, keywords in CATEGORY_RULES:
        if any(keyword in path_signal for keyword in keywords):
            return label

    text_signal = f"{title} {h1}".strip().lower()
    if text_signal:
        for label, keywords in CATEGORY_RULES:
            if any(keyword in text_signal for keyword in keywords):
                return label

    return "other"
