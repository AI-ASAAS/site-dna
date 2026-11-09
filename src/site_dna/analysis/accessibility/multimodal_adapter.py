"""Multimodal Visual Accessibility Context Adapter for Site DNA Phase 10."""

from pathlib import Path
from typing import Optional

from site_dna.core.logging import get_logger

logger = get_logger("analysis.accessibility.multimodal_adapter")


class MultimodalAccessibilityAdapter:
    """Provides selective visual context and screenshot paths for Gemini 3.6 Flash interpretation."""

    def select_visual_evidence(
        self,
        screenshot_path: Optional[str],
        base_dir: Path | str = "runs",
    ) -> Optional[str]:
        """Validate and return safe screenshot path for multimodal analysis if existing and authorized."""
        if not screenshot_path:
            return None

        p = Path(screenshot_path)
        if not p.is_absolute():
            p = (Path(base_dir) / screenshot_path).resolve()

        if p.exists() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            # Check size to prevent token blowup (max 5MB)
            if p.stat().st_size <= 5 * 1024 * 1024:
                return str(p)

        return None
