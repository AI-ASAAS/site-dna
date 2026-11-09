"""External performance metrics adapter (PageSpeed Insights / CrUX API).

This integration is optional, disabled by default, and isolated from core deterministic analysis.
"""

from typing import Optional

from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.technical_seo import ExternalMetricRecord

logger = get_logger("analysis.technical_seo.external_metrics")


class ExternalMetricsAdapter:
    """Safely queries external performance APIs when explicitly enabled and configured."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    def fetch_metrics(self, url: str) -> ExternalMetricRecord:
        """Fetch PageSpeed Insights or CrUX metrics if enabled, or return disabled status."""
        if not self.settings.technical_seo_external_metrics_enabled:
            return ExternalMetricRecord(
                provider="none",
                scope="not_available",
                metrics={},
                status="disabled",
            )

        # In standard secure default operation, external querying is disabled
        logger.info("External metrics adapter is disabled by policy for '%s'", url)
        return ExternalMetricRecord(
            provider="none",
            scope="not_available",
            metrics={},
            status="disabled",
        )
