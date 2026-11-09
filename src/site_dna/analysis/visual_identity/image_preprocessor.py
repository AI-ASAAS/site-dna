"""Image preprocessor managing screenshot loading, budgets, crops, and aspect-ratio integrity."""

import hashlib
import io
from pathlib import Path
from typing import Any, Optional

from PIL import Image
from pydantic import BaseModel, Field

from site_dna.core.logging import get_logger

logger = get_logger("analysis.visual_identity.image_preprocessor")


class PreparedImage(BaseModel):
    """Normalized, budget-managed image payload ready for Gemini multimodal transmission."""

    file_path: str
    page_url: str
    viewport_profile: str  # desktop or mobile
    screenshot_type: str  # viewport, full_page, or crop
    width_px: int
    height_px: int
    sha256: str
    image_bytes: bytes = Field(repr=False)
    mime_type: str = "image/png"
    crop_bounds: Optional[dict[str, int]] = None
    scale_factor: float = 1.0


class ImagePreprocessor:
    """Selects, validates, crops, and bundles screenshot images under a strict quota."""

    def __init__(
        self,
        max_images: int = 8,
        max_crop_height: int = 2400,
    ):
        self.max_images = max_images
        self.max_crop_height = max_crop_height

    def prepare_images(
        self,
        pages_context: list[Any],
        include_full_page: bool = True,
    ) -> list[PreparedImage]:
        """Select primary viewport screenshots first, followed by controlled full-page views."""
        prepared: list[PreparedImage] = []

        # Stage A: Collect primary viewport screenshots across eligible pages
        for page in pages_context:
            if len(prepared) >= self.max_images:
                break

            # Desktop viewport
            d_vp = next(
                (s for s in page.desktop_screenshots if s.get("screenshot_type") == "viewport" and s.get("success")),
                None,
            )
            if d_vp:
                prep = self._load_and_prepare(
                    file_path=d_vp["file_path"],
                    page_url=page.page_url,
                    viewport_profile="desktop",
                    screenshot_type="viewport",
                )
                if prep:
                    prepared.append(prep)

            if len(prepared) >= self.max_images:
                break

            # Mobile viewport
            m_vp = next(
                (s for s in page.mobile_screenshots if s.get("screenshot_type") == "viewport" and s.get("success")),
                None,
            )
            if m_vp:
                prep = self._load_and_prepare(
                    file_path=m_vp["file_path"],
                    page_url=page.page_url,
                    viewport_profile="mobile",
                    screenshot_type="viewport",
                )
                if prep:
                    prepared.append(prep)

        # Stage B: If budget remains and full-page is requested, add full-page or hero crops
        if include_full_page and len(prepared) < self.max_images:
            for page in pages_context:
                if len(prepared) >= self.max_images:
                    break

                d_fp = next(
                    (
                        s
                        for s in page.desktop_screenshots
                        if s.get("screenshot_type") == "full_page" and s.get("success")
                    ),
                    None,
                )
                if d_fp:
                    prep = self._load_and_prepare(
                        file_path=d_fp["file_path"],
                        page_url=page.page_url,
                        viewport_profile="desktop",
                        screenshot_type="full_page",
                    )
                    if prep:
                        prepared.append(prep)

        logger.info("Preprocessed %d images for multimodal analysis (budget: %d)", len(prepared), self.max_images)
        return prepared

    def _load_and_prepare(
        self,
        file_path: str,
        page_url: str,
        viewport_profile: str,
        screenshot_type: str,
    ) -> Optional[PreparedImage]:
        """Read image bytes, verify format and dimensions, and apply cropping if oversized."""
        p = Path(file_path)
        if not p.exists():
            logger.warning("Screenshot path does not exist: %s", file_path)
            return None

        try:
            raw_bytes = p.read_bytes()
            sha256 = hashlib.sha256(raw_bytes).hexdigest()

            with Image.open(io.BytesIO(raw_bytes)) as img:
                w, h = img.size

                # If full-page image is excessively tall, crop the upper primary region
                if h > self.max_crop_height and screenshot_type == "full_page":
                    crop_box = (0, 0, w, self.max_crop_height)
                    cropped_img = img.crop(crop_box)
                    buf = io.BytesIO()
                    cropped_img.save(buf, format="PNG")
                    crop_bytes = buf.getvalue()
                    crop_sha = hashlib.sha256(crop_bytes).hexdigest()

                    return PreparedImage(
                        file_path=str(p),
                        page_url=page_url,
                        viewport_profile=viewport_profile,
                        screenshot_type="crop",
                        width_px=w,
                        height_px=self.max_crop_height,
                        sha256=crop_sha,
                        image_bytes=crop_bytes,
                        mime_type="image/png",
                        crop_bounds={"x": 0, "y": 0, "width": w, "height": self.max_crop_height},
                    )

                return PreparedImage(
                    file_path=str(p),
                    page_url=page_url,
                    viewport_profile=viewport_profile,
                    screenshot_type=screenshot_type,
                    width_px=w,
                    height_px=h,
                    sha256=sha256,
                    image_bytes=raw_bytes,
                    mime_type="image/png",
                )
        except Exception as exc:
            logger.error("Failed to load image %s: %s", file_path, exc)
            return None
