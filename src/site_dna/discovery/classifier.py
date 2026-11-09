"""Heuristic page classifier supporting English and Arabic signals across URL, titles, and text."""

from urllib.parse import urlsplit

from site_dna.schemas.page import PageCategory

CATEGORY_SIGNALS: dict[PageCategory, dict[str, list[str]]] = {
    "contact": {
        "url": ["contact", "contact-us", "reach-us", "get-in-touch", "اتصل", "تواصل", "اتصل-بنا", "اتصل_بنا"],
        "title": ["contact", "get in touch", "اتصل بنا", "تواصل معنا", "خدمة العملاء"],
        "content": ["email", "phone", "address", "message", "هاتف", "بريد", "عنوان", "رسالة"],
    },
    "about": {
        "url": ["about", "about-us", "who-we-are", "company", "our-story", "من-نحن", "عنا", "عن-الشركة"],
        "title": ["about us", "who we are", "our story", "our team", "من نحن", "عن الشركة", "قصتنا", "فريقنا"],
        "content": ["mission", "vision", "founded", "history", "our values", "رؤيتنا", "رسالتنا", "قيمنا"],
    },
    "services": {
        "url": ["service", "services", "what-we-do", "capabilities", "خدمات", "خدماتنا"],
        "title": ["services", "our services", "what we do", "خدماتنا", "حلول وخدمات"],
        "content": ["consulting", "development", "managed", "offering", "استشارات", "تطوير", "خدمات"],
    },
    "products": {
        "url": ["product", "products", "solutions", "store", "shop", "منتجات", "منتجاتنا", "متجر"],
        "title": ["products", "solutions", "store", "shop", "منتجات", "متجر", "حلولنا"],
        "content": ["features", "specifications", "add to cart", "buy now", "شراء", "مواصفات", "سلة"],
    },
    "pricing": {
        "url": ["pricing", "price", "plans", "packages", "rates", "أسعار", "باقات", "خطط"],
        "title": ["pricing", "plans", "pricing plans", "packages", "الأسعار", "باقات الاشتراك", "خطط"],
        "content": ["per month", "billed annually", "free tier", "enterprise", "شهرياً", "سنوياً", "ريال", "$"],
    },
    "portfolio": {
        "url": ["portfolio", "projects", "work", "case-studies", "clients", "أعمالنا", "مشاريع", "عملاؤنا"],
        "title": ["portfolio", "our work", "case studies", "projects", "أعمالنا", "معرض الأعمال", "مشاريعنا"],
        "content": ["client", "challenge", "results", "delivered", "عميل", "نتائج", "دراسة حالة"],
    },
    "blog": {
        "url": ["blog", "news", "articles", "posts", "insights", "مدونة", "أخبار", "مقالات"],
        "title": ["blog", "latest news", "articles", "insights", "مدونة", "أحدث الأخبار", "مقالات"],
        "content": ["published on", "author", "read more", "min read", "بقلم", "تاريخ النشر", "قراءة المزيد"],
    },
    "faq": {
        "url": ["faq", "faqs", "help", "questions", "support", "الأسئلة-الشائعة", "مساعدة", "دعم"],
        "title": ["faq", "frequently asked questions", "help center", "الأسئلة الشائعة", "مركز المساعدة"],
        "content": ["how do i", "what is", "frequently asked", "question", "سؤال", "كيف يمكنني", "إجابة"],
    },
}


def classify_page(
    url: str,
    depth: int,
    title: str = "",
    h1_text: str = "",
    content_snippet: str = "",
) -> tuple[PageCategory, float]:
    """Classify a page into a strategic category using URL, titles, and content heuristics.

    Returns:
        (category, confidence_score) where confidence is between 0.0 and 1.0.
    """
    parts = urlsplit(url)
    path = parts.path.strip("/").lower()

    # Rule 1: Depth 0 or root path is Home
    if depth == 0 or not path or path in ("", "index.html", "index.php", "home", "en", "ar"):
        return "home", 0.95

    url_str = f"{path} {parts.query}".lower()
    header_str = f"{title} {h1_text}".lower()
    text_str = content_snippet[:500].lower()

    best_category: PageCategory = "other"
    highest_score = 0.0

    for category, signals in CATEGORY_SIGNALS.items():
        score = 0.0

        # Check URL signals (weight 0.45)
        url_matches = sum(1 for kw in signals["url"] if kw in url_str)
        if url_matches > 0:
            score += min(0.45, 0.35 + (url_matches * 0.05))

        # Check Title/H1 signals (weight 0.35)
        title_matches = sum(1 for kw in signals["title"] if kw in header_str)
        if title_matches > 0:
            score += min(0.35, 0.25 + (title_matches * 0.05))

        # Check Content signals (weight 0.20)
        content_matches = sum(1 for kw in signals["content"] if kw in text_str)
        if content_matches > 0:
            score += min(0.20, 0.10 + (content_matches * 0.05))

        if score > highest_score:
            highest_score = score
            best_category = category

    if highest_score >= 0.30:
        return best_category, round(min(1.0, highest_score), 2)

    return "other", 0.20
