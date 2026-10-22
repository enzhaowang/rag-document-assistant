"""Structured logging: one JSON object per line on stderr.

Usage:
    from app.logging_config import configure_logging
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("ingest finished", extra={"files": 12, "chunks": 240})

Any `extra` fields are emitted as top-level JSON keys next to the standard ones.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from app.config import get_settings

# Attributes present on every LogRecord; anything else came from `extra=` and is emitted.
_RESERVED_ATTRS = frozenset(
    vars(logging.LogRecord("", logging.INFO, "", 0, "", None, None)).keys()
) | {"message", "asctime", "taskName"}

_HANDLER_NAME = "app-json-stderr"


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED_ATTRS and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)
        return json.dumps(payload, default=str, ensure_ascii=False)


def configure_logging(level: str | None = None) -> None:
    """Install the JSON handler on the root logger.

    Safe to call more than once: the handler is only added the first time, later calls
    just update the level. `level` defaults to the LOG_LEVEL setting.
    """
    resolved_level = (level or get_settings().log_level).upper()
    root = logging.getLogger()
    root.setLevel(resolved_level)

    if not any(h.get_name() == _HANDLER_NAME for h in root.handlers):
        handler = logging.StreamHandler(sys.stderr)
        handler.set_name(_HANDLER_NAME)
        handler.setFormatter(JsonFormatter())
        root.addHandler(handler)
