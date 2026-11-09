"""Rendered DOM structure extraction collecting bounded semantic element records."""

from typing import Optional

from playwright.async_api import Page

from site_dna.core.config import Settings, get_settings
from site_dna.schemas.visual import DOMElementRecord

# Safe JavaScript evaluation script to extract bounded DOM records
DOM_EXTRACTION_SCRIPT = """
(maxElements) => {
  const selector = 'header, nav, main, section, article, aside, footer, h1, h2, h3, h4, h5, h6, p, a, button, img, form, label';
  const nodes = Array.from(document.querySelectorAll(selector)).slice(0, maxElements);

  return nodes.map((el, index) => {
    const rect = el.getBoundingClientRect();
    const style = window.getComputedStyle(el);
    const isVisible = rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';

    // Build simple stable path
    let path = el.tagName.toLowerCase();
    if (el.id) {
      path += '#' + el.id;
    } else if (el.parentElement) {
      const siblings = Array.from(el.parentElement.children).filter(c => c.tagName === el.tagName);
      if (siblings.length > 1) {
        path += ':nth-of-type(' + (siblings.indexOf(el) + 1) + ')';
      }
    }

    // Filter strictly safe attributes (NEVER collect input values, passwords, or tokens)
    const safeAttrs = {};
    const allowed = ['href', 'src', 'alt', 'role', 'type', 'dir', 'lang', 'target', 'action', 'method', 'aria-label'];
    for (const attr of allowed) {
      if (el.hasAttribute(attr)) {
        safeAttrs[attr] = el.getAttribute(attr);
      }
    }

    const text = (el.innerText || el.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 120);
    const accessibleName = el.getAttribute('aria-label') || el.getAttribute('alt') || (el.tagName === 'IMG' ? '' : text.slice(0, 50));

    return {
      element_id: 'el-' + index,
      tag_name: el.tagName.toLowerCase(),
      dom_path: path,
      semantic_role: el.getAttribute('role') || el.tagName.toLowerCase(),
      accessible_name: accessibleName || null,
      text_excerpt: text || null,
      visible: isVisible,
      bounding_box: {
        x: Math.round(rect.x),
        y: Math.round(rect.y),
        width: Math.round(rect.width),
        height: Math.round(rect.height)
      },
      parent_reference: el.parentElement ? el.parentElement.tagName.toLowerCase() : null,
      classes: Array.from(el.classList || []),
      attributes: safeAttrs
    };
  });
}
"""


class DOMExtractor:
    """Extracts bounded semantic DOM structure records from a rendered page."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    async def extract_dom_elements(self, page: Page) -> list[DOMElementRecord]:
        """Execute in-browser evaluation and return structured DOMElementRecords."""
        max_el = self.settings.visual_max_dom_elements
        raw_items = await page.evaluate(DOM_EXTRACTION_SCRIPT, max_el)

        return [DOMElementRecord(**item) for item in raw_items]
