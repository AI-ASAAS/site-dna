"""Safe, model-isolated disk cache for multimodal visual identity analysis results."""

import hashlib
import json
from pathlib import Path
from typing import Any, Optional

from site_dna.analysis.visual_identity.context_builder import VisualAnalysisContext
from site_dna.analysis.visual_identity.image_preprocessor import PreparedImage
from site_dna.core.logging import get_logger

logger = get_logger("analysis.visual_identity.cache")

PROMPT_VERSION = "v1.0"
SCHEMA_VERSION = "1.0"


class VisualIdentityCache:
    """Provides SHA-256 content-addressable caching keyed by model ID, inputs, and prompt version."""

    def __init__(self, cache_dir: str = "runs/cache", enabled: bool = True):
        self.cache_dir = Path(cache_dir)
        self.enabled = enabled
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def compute_cache_key(
        model_name: str,
        context: VisualAnalysisContext,
        images: list[PreparedImage],
    ) -> str:
        """Compute deterministic SHA-256 cache key strictly isolating model versions and inputs."""
        hasher = hashlib.sha256()

        # 1. Model ID and versions (ensures gemini-3.8-flash entries never collide with gemini-3.6-flash)
        hasher.update(model_name.strip().encode("utf-8"))
        hasher.update(b":")
        hasher.update(SCHEMA_VERSION.encode("utf-8"))
        hasher.update(b":")
        hasher.update(PROMPT_VERSION.encode("utf-8"))
        hasher.update(b":")

        # 2. Context identifier and structure
        hasher.update(context.target_origin.encode("utf-8"))
        hasher.update(b":")
        for page in sorted(context.pages, key=lambda p: p.page_url):
            hasher.update(page.page_url.encode("utf-8"))
            hasher.update(str(len(page.dom_elements)).encode("utf-8"))
            hasher.update(str(len(page.colors)).encode("utf-8"))
            hasher.update(str(len(page.typography)).encode("utf-8"))

        # 3. Image hashes
        hasher.update(b":images:")
        for img in images:
            hasher.update(img.sha256.encode("utf-8"))

        return hasher.hexdigest()

    def get(self, cache_key: str, expected_model: str) -> Optional[dict[str, Any]]:
        """Retrieve cached analysis if available, valid, and matching the expected model."""
        if not self.enabled:
            return None

        entry_path = self.cache_dir / f"{cache_key}.json"
        if not entry_path.exists():
            return None

        try:
            content = entry_path.read_text(encoding="utf-8")
            data = json.loads(content)
            # Model isolation verification
            if data.get("model_name") != expected_model:
                logger.warning(
                    "Cache entry model mismatch (cached=%s, expected=%s). Ignoring cache.",
                    data.get("model_name"),
                    expected_model,
                )
                return None

            data["from_cache"] = True
            logger.info("Visual identity cache hit: %s (model: %s)", cache_key[:12], expected_model)
            return data
        except Exception as exc:
            logger.warning("Failed to read cache entry %s: %s", cache_key, exc)
            return None

    def set(self, cache_key: str, data: dict[str, Any]) -> None:
        """Persist analysis result to cache."""
        if not self.enabled:
            return

        entry_path = self.cache_dir / f"{cache_key}.json"
        try:
            temp_path = self.cache_dir / f"{cache_key}.tmp.{Path().stat().st_mtime if entry_path.exists() else 'new'}"
            temp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            temp_path.replace(entry_path)
            logger.info("Persisted visual identity result to cache: %s", cache_key[:12])
        except Exception as exc:
            logger.warning("Failed to write cache entry %s: %s", cache_key, exc)
