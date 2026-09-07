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
# Where console-only mode is desired, pass file_path=None explicitly. By
# default every feature's log propagates to the root logger and is mirrored
# into logs/{app_env}.log alongside stdout.
DEFAULT_LOG_FILE: str = "logs/dev.log"
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


def _is_writable_location(path: str) -> bool:
    """Return True if ``path`` sits on a writable filesystem.

    Serverless platforms (Vercel) mount read-only filesystems; probing avoids a
    mid-attempt RotatingFileHandler failure and keeps those logs on the console.
    """
    try:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8"):
            pass
        return True
    except OSError:
        return False


def _add_file_handler(path: str, *, max_bytes: int, backup_count: int) -> None:
    """Add a rotating file handler for ``path`` if not already installed.

    Idempotent per path: repeated calls (tests, reload) do not stack handlers.
    When the target filesystem is read-only, no handler is attached and the
    request is skipped (logs stay on the console).

    Args:
        path: Absolute or relative log file path.
        max_bytes: Rotate when the file exceeds this many bytes.
        backup_count: Number of rotated backups to keep.
    """
    if path in _installed_files:
        return
    if not _is_writable_location(path):
        return
    try:
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
    except Exception as exc:  # noqa: BLE001 - logging must never crash the app
        logging.warning("File logging unavailable on this filesystem; using console only: %s", exc)


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

    Configured ``configure_logging`` mirrors every log record — from all
    feature modules — to stdout and (by default) to ``logs/{app_env}.log``.
    Because child loggers propagate to the configured root logger, request
    logs, agent activity, services, and tools all land in the same file.

    Args:
        level: The minimum log level to emit, as an int or level name
            (e.g. ``"DEBUG"``, ``"INFO"``). Strings are resolved via
            :func:`logging.getLevelName`.
        file_path: Path for a local rotating file handler. Pass ``None`` for
            console-only output. Defaults to ``logs/dev.log``. On read-only
            filesystems (e.g. Vercel's ``/var/task``), the file handler is
            skipped silently and logs flow to the console, which serverless
            platforms collect.
        max_bytes: Rotate the file handler at this size (bytes).
        backup_count: Number of rotated file backups to keep.
        verbose: When True, keep uvicorn access/error logs at INFO so every
            request appears in the console/file (development). When False,
            throttle uvicorn's access logger to WARNING for quieter output.
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
