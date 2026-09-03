"""Centralized structured logging configuration.

Provides a single :func:`configure_logging` entry point that sets JSON-ish,
request-ids, and consistent formatting regardless of environment. On
serverless (e.g. Vercel) plain text logs are fine, but we still keep the
format stable and add a ``request_id`` when present in context.
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

_LOG_FORMAT = (
    "%(asctime)s %(levelname)s %(name)s [%(request_id)s] "
    "%(message)s"
)


class RequestIdFilter(logging.Filter):
    """Attach the current request id to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Inject the request id into the log record."""
        record.request_id = request_id_var.get() or "-"
        return True


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging for the application.

    Idempotent: re-running this does not duplicate handlers.

    Args:
        level: The minimum log level to emit.
    """
    root = logging.getLogger()
    # Avoid stacking duplicate handlers on repeated calls (tests, reload).
    for handler in list(root.handlers):
        if isinstance(handler, _MarkerHandler):
            return
    root.setLevel(level)
    handler = _MarkerHandler()
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    handler.addFilter(RequestIdFilter())
    root.addHandler(handler)

    # Keep third-party loggers from being overly chatty on serverless.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


class _MarkerHandler(logging.StreamHandler):
    """Sentinel handler type so configure_logging is idempotent."""

    def __init__(self) -> None:
        super().__init__(sys.stdout)
