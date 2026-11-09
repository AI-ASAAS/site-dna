"""Heuristic page classification engine for Content & Marketing Intelligence."""

from urllib.parse import urlparse

from site_dna.schemas.content_marketing import PageContentRecord


class PageClassifier:
    """Classifies website pages into functional content archetypes."""

    @staticmethod
    def classify_page(record: PageContentRecord) -> str:
        """Classify page into: home, about, services, products, pricing, contact, blog, faq, other."""
        if record.page_type and record.page_type not in ("unknown", "other"):
            return record.page_type

        url_lower = record.page_url.lower()
        path = urlparse(url_lower).path.strip("/")
        title_lower = (record.page_title or "").lower()
        headings_text = " ".join(h.get("text", "").lower() for h in record.headings)

        # 1. Homepage
        if not path or path in ("", "index.html", "index.php", "home"):
            return "home"

        # 2. Contact
        if any(
            term in path or term in title_lower or term in headings_text
            for term in ["contact", "اتصل", "تواصل", "support", "get-in-touch"]
        ):
            return "contact"

        # 3. About
        if any(
            term in path or term in title_lower or term in headings_text
            for term in ["about", "من نحن", "من-نحن", "عن-الشركة", "عن الشركة", "who-we-are", "team"]
        ):
            return "about"

        # 4. Pricing
        if any(
            term in path or term in title_lower or term in headings_text
            for term in ["pricing", "plans", "أسعار", "باقات", "price", "cost"]
        ):
            return "pricing"

        # 5. Products
        if any(
            term in path or term in title_lower or term in headings_text
            for term in ["product", "products", "منتج", "منتجات", "features", "مميزات"]
        ):
            return "products"

        # 6. Services / Solutions
        if any(
            term in path or term in title_lower or term in headings_text
            for term in ["service", "services", "خدمة", "خدمات", "solution", "solutions", "حلول"]
        ):
            return "services"

        # 7. FAQ / Help
        if any(
            term in path or term in title_lower or term in headings_text
            for term in ["faq", "help", "أسئلة", "الأسئلة-الشائعة", "support"]
        ):
            return "faq"

        # 8. Blog / Articles
        if any(
            term in path or term in title_lower or term in headings_text
            for term in ["blog", "article", "articles", "news", "مدونة", "أخبار", "posts"]
        ):
            return "blog"

        return "other"
