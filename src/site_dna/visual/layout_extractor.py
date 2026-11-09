"""Layout geometry extractor capturing bounding boxes, spatial coordinates, and flex/grid structures."""

from typing import Optional

from playwright.async_api import Page

from site_dna.core.config import Settings, get_settings
from site_dna.schemas.visual import LayoutRecord

LAYOUT_EXTRACTION_SCRIPT = """
() => {
  const sections = [];

  // 1. Header
  const header = document.querySelector('header');
  if (header) {
    const rect = header.getBoundingClientRect();
    const style = window.getComputedStyle(header);
    sections.push({
      section_type: 'header',
      element_id: 'sec-header',
      bounding_box: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
      display: style.display,
      position: style.position,
      is_visible: rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden',
      grid_flex_properties: {
        flex_direction: style.flexDirection,
        justify_content: style.justifyContent,
        gap: style.gap
      }
    });
  }

  // 2. Navigation
  const nav = document.querySelector('nav');
  if (nav) {
    const rect = nav.getBoundingClientRect();
    const style = window.getComputedStyle(nav);
    sections.push({
      section_type: 'nav',
      element_id: 'sec-nav',
      bounding_box: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
      display: style.display,
      position: style.position,
      is_visible: rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden',
      grid_flex_properties: {
        display: style.display,
        gap: style.gap
      }
    });
  }

  // 3. Hero candidate (first section/main container with H1)
  const h1 = document.querySelector('h1');
  if (h1) {
    const heroContainer = h1.closest('section, main, div') || h1;
    const rect = heroContainer.getBoundingClientRect();
    const style = window.getComputedStyle(heroContainer);
    sections.push({
      section_type: 'hero_candidate',
      element_id: 'sec-hero',
      bounding_box: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
      display: style.display,
      position: style.position,
      is_visible: rect.width > 0 && rect.height > 0,
      grid_flex_properties: {
        display: style.display,
        align_items: style.alignItems
      }
    });
  }

  // 4. Footer
  const footer = document.querySelector('footer');
  if (footer) {
    const rect = footer.getBoundingClientRect();
    const style = window.getComputedStyle(footer);
    sections.push({
      section_type: 'footer',
      element_id: 'sec-footer',
      bounding_box: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
      display: style.display,
      position: style.position,
      is_visible: rect.width > 0 && rect.height > 0,
      grid_flex_properties: {
        display: style.display
      }
    });
  }

  return sections;
}
"""


class LayoutExtractor:
    """Extracts bounding box geometry and flex/grid layout properties for key sections."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    async def extract_layout(self, page: Page) -> list[LayoutRecord]:
        """Collect spatial and layout metrics from candidate sections."""
        raw_sections = await page.evaluate(LAYOUT_EXTRACTION_SCRIPT)
        return [LayoutRecord(**sec) for sec in raw_sections]
