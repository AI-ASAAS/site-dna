"""Typography extractor capturing font family, sizes, weights, and RTL text directions."""

from typing import Optional

from playwright.async_api import Page

from site_dna.core.config import Settings, get_settings
from site_dna.schemas.visual import TypographyRecord

TYPOGRAPHY_EXTRACTION_SCRIPT = """
(viewportName) => {
  const selector = 'h1, h2, h3, h4, h5, h6, p, nav a, button, .btn';
  const nodes = Array.from(document.querySelectorAll(selector)).slice(0, 50);

  return nodes.map((el, index) => {
    const style = window.getComputedStyle(el);
    const fontSizePx = parseFloat(style.fontSize) || 16;
    const lineHeightVal = style.lineHeight;
    const lineHeightPx = lineHeightVal.endsWith('px') ? parseFloat(lineHeightVal) : null;

    const dir = style.direction || el.getAttribute('dir') || document.documentElement.getAttribute('dir') || 'ltr';
    const lang = el.getAttribute('lang') || document.documentElement.getAttribute('lang') || null;

    return {
      element_type: el.tagName.toLowerCase(),
      font_family: style.fontFamily,
      font_size_px: fontSizePx,
      font_weight: style.fontWeight,
      line_height_px: lineHeightPx,
      letter_spacing: style.letterSpacing !== 'normal' ? style.letterSpacing : null,
      text_align: style.textAlign,
      text_transform: style.textTransform !== 'none' ? style.textTransform : null,
      direction: dir,
      language: lang,
      viewport: viewportName,
      element_id: 'el-' + index
    };
  });
}
"""


class TypographyExtractor:
    """Extracts typography stacks, scale, line-heights, and directionality."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    async def extract_typography(
        self,
        page: Page,
        viewport_name: str = "desktop",
    ) -> list[TypographyRecord]:
        """Collect typography records for representative text elements."""
        raw_items = await page.evaluate(TYPOGRAPHY_EXTRACTION_SCRIPT, viewport_name)

        # Deduplicate identical typography definitions per element type and viewport
        seen: set[tuple[str, str, float, str]] = set()
        records: list[TypographyRecord] = []

        for item in raw_items:
            key = (item["element_type"], item["font_family"], item["font_size_px"], viewport_name)
            if key not in seen:
                seen.add(key)
                records.append(TypographyRecord(**item))

        return records
