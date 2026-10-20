"""Structured logging setup.

Machine-parseable JSON to stderr. A redaction processor blanks anything that looks like
a secret and truncates oversized strings, so prompt/completion content and API keys can
never reach the logs (FR-036).
"""

from __future__ import annotations

import logging
import sys
from collections.abc import MutableMapping
from typing import Any

import structlog

_SECRET_KEYS = {
    "api_key",
    "admin_api_key",
    "x-api-key",
    "authorization",
    "auth",
    "token",
    "db_key",
    "password",
    "secret",
}
_MAX_STR = 2000


def _redact(
    _logger: Any, _method: str, event: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    for key, value in list(event.items()):
        if key.lower() in _SECRET_KEYS:
            event[key] = "***redacted***"
        elif isinstance(value, str) and len(value) > _MAX_STR:
            event[key] = value[:_MAX_STR] + "...<truncated>"
    return event


def configure_logging(level: str = "info") -> None:
    logging.basicConfig(format="%(message)s", stream=sys.stderr, level=level.upper())
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _redact,
            structlog.processors.JSONRenderer(sort_keys=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(level.upper())
        ),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "tokenpulse") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
