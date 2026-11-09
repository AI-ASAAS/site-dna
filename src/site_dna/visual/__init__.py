"""Visual evidence and browser rendering subsystem for Site DNA."""

from site_dna.visual.browser_manager import BrowserManager
from site_dna.visual.browser_security import BrowserSecurityPolicy
from site_dna.visual.color_extractor import ColorExtractor
from site_dna.visual.css_extractor import CSSExtractor
from site_dna.visual.dom_extractor import DOMExtractor
from site_dna.visual.evidence import VisualEvidenceCollector
from site_dna.visual.layout_extractor import LayoutExtractor
from site_dna.visual.renderer import PageRenderer, RenderResult
from site_dna.visual.responsive import ResponsiveAnalyzer
from site_dna.visual.screenshots import ScreenshotCapture
from site_dna.visual.service import VisualCollectionService
from site_dna.visual.storage import VisualStorageManager, generate_safe_page_id

__all__ = [
    "BrowserManager",
    "BrowserSecurityPolicy",
    "PageRenderer",
    "RenderResult",
    "ScreenshotCapture",
    "DOMExtractor",
    "CSSExtractor",
    "ColorExtractor",
    "LayoutExtractor",
    "ResponsiveAnalyzer",
    "VisualEvidenceCollector",
    "VisualStorageManager",
    "generate_safe_page_id",
    "VisualCollectionService",
]
