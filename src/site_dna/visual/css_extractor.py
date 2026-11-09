"""Computed CSS extractor collecting rendered style declarations from DOM elements."""

from typing import Optional

from playwright.async_api import Page

from site_dna.core.config import Settings, get_settings
from site_dna.schemas.visual import ComputedStyleRecord

CSS_EXTRACTION_SCRIPT = """
(maxElements) => {
  const selector = 'body, header, nav, h1, h2, h3, h4, p, a, button, footer, main, section, .btn';
  const nodes = Array.from(document.querySelectorAll(selector)).slice(0, maxElements);

  return nodes.map((el, index) => {
    const style = window.getComputedStyle(el);
    return {
      element_id: 'el-' + index,
      tag_name: el.tagName.toLowerCase(),
      color: style.color || null,
      background_color: style.backgroundColor || null,
      border_color: style.borderColor || null,
      font_family: style.fontFamily || null,
      font_size: style.fontSize || null,
      font_weight: style.fontWeight || null,
      line_height: style.lineHeight || null,
      display: style.display || null,
      position: style.position || null,
      border_radius: style.borderRadius !== '0px' ? style.borderRadius : null,
      box_shadow: style.boxShadow !== 'none' ? style.boxShadow : null,
      viewport: 'desktop'
    };
  });
}
"""


class CSSExtractor:
    """Extracts computed CSS style properties using window.getComputedStyle."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    async def extract_computed_styles(
        self,
        page: Page,
        viewport_name: str = "desktop",
    ) -> list[ComputedStyleRecord]:
        """Collect computed CSS declarations for representative rendered elements."""
        max_el = self.settings.visual_max_dom_elements
        raw_styles = await page.evaluate(CSS_EXTRACTION_SCRIPT, max_el)

        records: list[ComputedStyleRecord] = []
        for item in raw_styles:
            item["viewport"] = viewport_name
            records.append(ComputedStyleRecord(**item))
        return records
