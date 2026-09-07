"""Request-scoped logging context middleware.

Assigns a ``request_id`` per request (from the ``X-Request-ID`` header if the
client supplies one, otherwise a generated id) and exposes it in logs via the
``request_id_var`` context variable. The same id is echoed back in the
response ``X-Request-ID`` header so server errors can be correlated with logs.

When ``log_requests`` is enabled (default in development), each completed
request is logged with its method, path, status code, and duration so the
console/file shows human-readable access logs without relying on uvicorn's
logger.
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.logging import request_id_var

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a per-request id and populate the logging context variable."""

    def __init__(self, app, *, log_requests: bool = False):  # type: ignore[no-untyped-def]
        """Create the middleware.

        Args:
            app: The ASGI application to wrap.
            log_requests: When True, emit one INFO log line per request with
                method, path, status, and duration.
        """
        super().__init__(app)
        self.log_requests = log_requests

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        """Wrap the request with a request-id logging context.

        Args:
            request: The incoming ASGI request.
            call_next: The next middleware/application in the chain.

        Returns:
            The response with an ``X-Request-ID`` header set.
        """
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
        request.state.request_id = request_id
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)

        duration_ms = (time.perf_counter() - started) * 1000
        response.headers["X-Request-ID"] = request_id

        if self.log_requests:
            logger.info(
                "%s %s -> %s (%.1f ms)",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
            )
        return response
