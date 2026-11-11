"""Logging configuration and observability helpers for Site DNA."""

import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class SensitiveDataFilter(logging.Filter):
    """Filter that sanitizes common API key and token patterns from log records."""

    _PATTERNS = [
        re.compile(r"(AIzaSy[0-9A-Za-z_-]{33})"),
        re.compile(r"(AQ\.[0-9A-Za-z_-]{20,})"),
        re.compile(r"(Bearer\s+)[0-9A-Za-z_\.\-~+/=]+", re.IGNORECASE),
        re.compile(r"(api[-_]?key\s*[:=]\s*['\"]?)([^'\";\s]+)(['\"]?)", re.IGNORECASE),
        re.compile(r"([?&]key=)([^&\s\"']+)", re.IGNORECASE),
    ]

    @classmethod
    def _sanitize(cls, value: str) -> str:
        sanitized = value
        for pattern in cls._PATTERNS:
            sanitized = pattern.sub(r"\1***REDACTED***", sanitized)
        return sanitized

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self._sanitize(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(
                self._sanitize(arg) if isinstance(arg, str) else arg for arg in record.args
            )
        elif isinstance(record.args, dict):
            record.args = {
                key: self._sanitize(value) if isinstance(value, str) else value
                for key, value in record.args.items()
            }
        return True


class RunContextFilter(logging.Filter):
    """Injects contextual attributes like run_id into records if not already present."""

    def __init__(self, run_id: Optional[str] = None):
        super().__init__()
        self.run_id = run_id or "-"

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "run_id"):
            record.run_id = self.run_id
        return True


def setup_logging(
    level: str = "INFO",
    run_id: Optional[str] = None,
) -> None:
    """Configure structured logging for the application.

    Ensures consistent timestamp, level, component name, and run_id format,
    while applying redaction filters for secrets.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Format: [timestamp] [level] [run_id] [name] - message
    log_format = "%(asctime)s [%(levelname)s] [run_id=%(run_id)s] [%(name)s] %(message)s"
    formatter = logging.Formatter(fmt=log_format, datefmt="%Y-%m-%d %H:%M:%S")

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(SensitiveDataFilter())
    handler.addFilter(RunContextFilter(run_id=run_id))

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers to avoid duplicates
    if root_logger.handlers:
        root_logger.handlers.clear()

    root_logger.addHandler(handler)

    # Silence overly verbose third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)


class JsonLineFormatter(logging.Formatter):
    """Render log records as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        run_id = getattr(record, "run_id", None)
        if run_id:
            payload["run_id"] = run_id
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_scan_logging(
    scan_id: str,
    storage_dir: str | Path = "storage",
    level: str = "INFO",
    stderr: bool = True,
) -> Path:
    """Configure JSON-lines scan logging plus optional human-readable stderr output.

    Returns the path to ``storage/{scan_id}/scan.log``. Both handlers apply the
    secret redaction filter, so API keys and ``key=`` query parameters never
    reach disk or the console.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    scan_dir = Path(storage_dir) / scan_id
    scan_dir.mkdir(parents=True, exist_ok=True)
    log_path = scan_dir / "scan.log"

    json_handler = logging.FileHandler(log_path, encoding="utf-8")
    json_handler.setFormatter(JsonLineFormatter())
    json_handler.addFilter(SensitiveDataFilter())
    json_handler.addFilter(RunContextFilter(run_id=scan_id))

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    if root_logger.handlers:
        root_logger.handlers.clear()
    root_logger.addHandler(json_handler)

    if stderr:
        human_handler = logging.StreamHandler(sys.stderr)
        human_handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] [run_id=%(run_id)s] [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        human_handler.addFilter(SensitiveDataFilter())
        human_handler.addFilter(RunContextFilter(run_id=scan_id))
        root_logger.addHandler(human_handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)

    return log_path


def get_logger(name: str) -> logging.Logger:
    """Return a standard application logger."""
    return logging.getLogger(name)
