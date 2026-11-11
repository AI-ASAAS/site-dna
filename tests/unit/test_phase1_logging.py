"""Phase 1 logging redaction and JSON-lines scan log tests."""

import json
import logging

from site_dna.core.logging import SensitiveDataFilter, setup_scan_logging


def _make_record(message: str) -> logging.LogRecord:
    return logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=None,
        exc_info=None,
    )


def test_sensitive_filter_redacts_key_query_parameter() -> None:
    record = _make_record(
        "GET https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        "?url=https%3A%2F%2Fexample.com&strategy=mobile&key=SECRET123"
    )

    SensitiveDataFilter().filter(record)

    message = record.getMessage()
    assert "SECRET123" not in message
    assert "key=***REDACTED***" in message
    assert "strategy=mobile" in message


def test_sensitive_filter_redacts_api_keys_in_args() -> None:
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request failed: %s",
        args=("https://example.com/?key=SECRET456",),
        exc_info=None,
    )

    SensitiveDataFilter().filter(record)

    assert "SECRET456" not in record.getMessage()
    assert "***REDACTED***" in record.getMessage()


def test_scan_logging_writes_json_lines_with_redaction(tmp_path) -> None:
    root = logging.getLogger()
    original_handlers = list(root.handlers)
    try:
        log_path = setup_scan_logging("scan123", tmp_path, level="INFO")
        logging.getLogger("site_dna.scan.test").info(
            "calling https://www.googleapis.com/pagespeedonline/v5/runPagespeed?key=SECRET789"
        )
        for handler in root.handlers:
            handler.flush()

        lines = log_path.read_text(encoding="utf-8").strip().splitlines()
        assert lines
        payload = json.loads(lines[-1])
        assert payload["level"] == "INFO"
        assert payload["logger"] == "site_dna.scan.test"
        assert "SECRET789" not in payload["message"]
        assert "***REDACTED***" in payload["message"]
        assert "timestamp" in payload
    finally:
        root.handlers.clear()
        root.handlers.extend(original_handlers)
