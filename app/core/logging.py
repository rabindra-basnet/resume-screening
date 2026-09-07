"""Centralized structured logging configuration.

Provides a single :func:`configure_logging` entry point that sets JSON-ish,
request-ids, and consistent formatting regardless of environment. Logs go to
stdout (the stream is what serverless platforms like Vercel collect) and,
optionally when a ``file_path`` is supplied, to a local rotating file (useful
for development). Environments can opt into ``verbose`` mode, which keeps
uvicorn's per-request access logs visible instead of throttling them.

Every record is stamped with the current ``request_id`` context variable so a
request's logs can be correlated from middleware to handler to exceptions.
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from pathlib import Path

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

_LOG_FORMAT = (
    "%(asctime)s %(levelname)s %(name)s [%(request_id)s] "
    "%(message)s"
)

_installed_files: set[str] = set()

# Defaults baked into the config — these are the defaults unless explicitly
# overridden at the call site (no env vars required).
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FILE: str | None = None
DEFAULT_LOG_FILE_MAX_BYTES = 10 * 1024 * 1024
DEFAULT_LOG_FILE_BACKUP_COUNT = 3
DEFAULT_VERBOSE = False


class RequestIdFilter(logging.Filter):
    """Attach the current request id to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Inject the request id into the log record."""
        record.request_id = request_id_var.get() or "-"
        return True


def _new_handler() -> _MarkerHandler:
    """Build a stream handler stamped with the request-id filter."""
    handler = _MarkerHandler()
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    handler.addFilter(RequestIdFilter())
    return handler


def _add_file_handler(path: str, *, max_bytes: int, backup_count: int) -> None:
    """Add a rotating file handler for ``path`` if not already installed.

    Idempotent per path: repeated calls (tests, reload) do not stack handlers.

    Args:
        path: Absolute or relative log file path.
        max_bytes: Rotate when the file exceeds this many bytes.
        backup_count: Number of rotated backups to keep.
    """
    if path in _installed_files:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        target,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    handler.addFilter(RequestIdFilter())
    logging.getLogger().addHandler(handler)
    _installed_files.add(path)


def configure_logging(
    level: int | str = DEFAULT_LOG_LEVEL,
    *,
    file_path: str | None = DEFAULT_LOG_FILE,
    max_bytes: int = DEFAULT_LOG_FILE_MAX_BYTES,
    backup_count: int = DEFAULT_LOG_FILE_BACKUP_COUNT,
    verbose: bool = DEFAULT_VERBOSE,
) -> None:
    """Configure root logging for the application.

    Idempotent: re-running this does not duplicate handlers.

    Args:
        level: The minimum log level to emit, as an int or level name
            (e.g. ``"DEBUG"``, ``"INFO"``). Strings are resolved via
            :func:`logging.getLevelName`.
        file_path: Optional path for a local rotating file handler.
        max_bytes: Rotate the file handler at this size (bytes).
        backup_count: Number of rotated file backups to keep.
        verbose: When True, keep uvicorn access/error logs at INFO so every
            request appears in the console (development). When False, throttle
            uvicorn's access logger to WARNING for quieter serverless output.
    """
    if isinstance(level, str):
        level = logging.getLevelName(level.upper())
    root = logging.getLogger()
    # Avoid stacking duplicate handlers on repeated calls (tests, reload).
    for handler in list(root.handlers):
        if isinstance(handler, _MarkerHandler):
            root.setLevel(level)
            break
    else:
        root.setLevel(level)
        root.addHandler(_new_handler())

    if file_path:
        _add_file_handler(file_path, max_bytes=max_bytes, backup_count=backup_count)

    # Keep third-party loggers from being overly chatty on serverless.
    access = logging.getLogger("uvicorn.access")
    access.setLevel(logging.INFO if verbose else logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO if verbose else logging.WARNING)


class _MarkerHandler(logging.StreamHandler):
    """Sentinel handler type so configure_logging is idempotent."""

    def __init__(self) -> None:
        super().__init__(sys.stdout)
