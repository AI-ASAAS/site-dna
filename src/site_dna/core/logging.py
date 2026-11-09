"""Logging configuration and observability helpers for Site DNA."""

import logging
import re
import sys
from typing import Optional


class SensitiveDataFilter(logging.Filter):
    """Filter that sanitizes common API key and token patterns from log records."""

    _PATTERNS = [
        re.compile(r"(AIzaSy[0-9A-Za-z_-]{33})"),
        re.compile(r"(AQ\.[0-9A-Za-z_-]{20,})"),
        re.compile(r"(Bearer\s+)[0-9A-Za-z_\.\-~+/=]+", re.IGNORECASE),
        re.compile(r"(api[-_]?key\s*[:=]\s*['\"]?)([^'\";\s]+)(['\"]?)", re.IGNORECASE),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            sanitized = record.msg
            for pattern in self._PATTERNS:
                sanitized = pattern.sub(r"\1***REDACTED***", sanitized)
            record.msg = sanitized
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


def get_logger(name: str) -> logging.Logger:
    """Return a standard application logger."""
    return logging.getLogger(name)
