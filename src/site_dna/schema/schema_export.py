"""JSON Schema export for the Website Intelligence report (Phase 8)."""

import json
from pathlib import Path
from typing import Any

from site_dna.models.report import Report

SCHEMA_VERSION = "https://json-schema.org/draft/2020-12/schema"
DEFAULT_SCHEMA_PATH = Path(__file__).with_name("report.schema.json")


def build_schema() -> dict[str, Any]:
    """Return the report JSON Schema generated from the Pydantic model."""
    schema = Report.model_json_schema()
    schema["$schema"] = SCHEMA_VERSION
    return schema


def export_schema(path: str | Path | None = None) -> Path:
    """Write the report schema as stable UTF-8 JSON and return its path."""
    destination = Path(path) if path is not None else DEFAULT_SCHEMA_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(build_schema(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return destination
