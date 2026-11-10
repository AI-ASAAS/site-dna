"""Shared runtime context passed to every scan module."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from site_dna.core.config import ScanConfig, Settings


@dataclass
class ScanContext:
    """Per-run context carrying configuration, identity, logging, and timings."""

    config: ScanConfig
    settings: Settings
    scan_id: str
    output_dir: Path
    logger: logging.Logger
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    timings: dict[str, float] = field(default_factory=dict)
    http: Any | None = None
