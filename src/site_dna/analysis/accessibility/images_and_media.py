"""Non-Text Content, Images & Media Accessibility Analyzer for Site DNA Phase 10."""

from typing import Any

from bs4 import BeautifulSoup, Tag

from site_dna.schemas.accessibility import (
    AccessibilityPageRecord,
    ImagesMediaAssessment,
)


class ImagesMediaAnalyzer:
    """Evaluates text alternatives for images, SVGs, functional icons, and media elements."""

    def analyze(
        self,
        pages: Any,
        crawl_dataset: Any = None,
    ) -> ImagesMediaAssessment:
        """Audit image alt attributes, decorative status, SVG accessibility, and media tracks."""
        if isinstance(pages, str):
            p = AccessibilityPageRecord(page_url="https://example.com/test", page_title="Test Page")
            pages_list = [p]
            crawl_dataset = {"pages": [{"url": "https://example.com/test", "raw_html": pages}]}
        else:
            pages_list = pages or []
            crawl_dataset = crawl_dataset or {}

        total_images = 0
        decorative_images = 0
        informative_images = 0
        missing_alt = 0
        icon_buttons_no_name = 0
        svgs_no_title = 0
        videos_count = 0
        videos_with_captions = 0
        manual_reviews = 0
        evidence_ids: list[str] = []

        raw_pages_map = {p.get("url"): p for p in crawl_dataset.get("pages", [])}

        for page in pages_list:
            raw_p = raw_pages_map.get(page.page_url, {})
            html = raw_p.get("raw_html") or raw_p.get("html") or ""
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")

            # 1. Inspect <img> tags
            imgs = soup.find_all("img")
            total_images += len(imgs)

            for idx, img in enumerate(imgs):
                if not isinstance(img, Tag):
                    continue

                is_functional = False
                parent = img.find_parent(["a", "button"])
                if parent:
                    # Check if image is sole content in link/button
                    parent_text = parent.get_text(strip=True)
                    if not parent_text and not parent.get("aria-label"):
                        is_functional = True

                if not img.has_attr("alt"):
                    missing_alt += 1
                    evidence_ids.append(f"ev-img-missing-alt-{page.page_url[:30]}-{idx}")
                    if is_functional:
                        icon_buttons_no_name += 1
                else:
                    alt_val = img["alt"].strip()
                    if alt_val == "":
                        decorative_images += 1
                        # If functional image has empty alt, that's an inaccessible control!
                        if is_functional:
                            icon_buttons_no_name += 1
                            evidence_ids.append(f"ev-img-empty-alt-functional-{page.page_url[:30]}-{idx}")
                    else:
                        informative_images += 1
                        # Flag suspicious alt text for manual review (e.g. filename, generic word 'image')
                        if alt_val.lower() in ("image", "picture", "photo", "صورة", "graphic") or "." in alt_val[-5:]:
                            manual_reviews += 1
                            evidence_ids.append(f"ev-img-suspicious-alt-{page.page_url[:30]}-{idx}")

            # 2. Inspect <svg> elements
            svgs = soup.find_all("svg")
            for idx, svg in enumerate(svgs):
                if not isinstance(svg, Tag):
                    continue

                if svg.get("aria-hidden") == "true":
                    continue

                has_title = bool(svg.find("title")) or bool(svg.get("aria-label")) or bool(svg.get("aria-labelledby"))
                parent = svg.find_parent(["button", "a"])

                if not has_title:
                    svgs_no_title += 1
                    if parent and not parent.get_text(strip=True) and not parent.get("aria-label"):
                        icon_buttons_no_name += 1
                        evidence_ids.append(f"ev-svg-unnamed-icon-btn-{page.page_url[:30]}-{idx}")

            # 3. Inspect <video> and <audio>
            videos = soup.find_all("video")
            videos_count += len(videos)
            for idx, v in enumerate(videos):
                if not isinstance(v, Tag):
                    continue
                tracks = v.find_all("track", attrs={"kind": lambda k: k in ("captions", "subtitles")})
                if tracks:
                    videos_with_captions += 1
                    evidence_ids.append(f"ev-media-captions-found-{page.page_url[:30]}-{idx}")
                else:
                    manual_reviews += 1
                    evidence_ids.append(f"ev-media-no-captions-{page.page_url[:30]}-{idx}")

        return ImagesMediaAssessment(
            total_images=total_images,
            decorative_images_count=decorative_images,
            informative_images_count=informative_images,
            missing_alt_count=missing_alt,
            functional_icon_buttons_without_name=icon_buttons_no_name,
            svg_elements_without_title=svgs_no_title,
            videos_count=videos_count,
            videos_with_captions_observed=videos_with_captions,
            manual_media_reviews_needed=manual_reviews,
            evidence_ids=list(set(evidence_ids)),
        )
