"""HTTP error handling helpers.

Defines a small exception hierarchy and a generic exception handler that
turns unexpected failures into a consistent JSON shape without leaking
internals, while still logging the full traceback server-side.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

_API_ERROR_FIELDS: tuple[str, ...] = (
    "error",
    "error_description",
    "error_uri",
)

STANDARD_ERROR_BODY: dict[str, Any] = {
    "error": "internal_error",
    "error_description": "An unexpected error occurred. Please try again later.",
}


def register_exception_handlers(app: FastAPI) -> None:
    """Attach JSON exception handlers to ``app``.

    Handlers:
        * Validation errors -> 422 with field detail.
        * Unhandled exceptions -> 500 with generic body (traceback logged).
        * Authlib ``::OAuthError`` (normalized below) -> 400/401.

    Args:
        app: The FastAPI application to register handlers on.
    """
    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled error on %s %s", request.method, request.url.path
        )
        body = dict(STANDARD_ERROR_BODY)
        # Preserve OAuth error detail for actionable feedback to the client.
        for field in _API_ERROR_FIELDS:
            value = getattr(exc, field, None)
            if value is None and field == "error_description":
                value = getattr(exc, "description", None)
            if value:
                body[field] = str(value)
        return JSONResponse(status_code=500, content=body)

    @app.exception_handler(RequestValidationError)
    async def _validation(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning(
            "Validation error on %s %s: %s",
            request.method,
            request.url.path,
            exc.errors(),
        )
        return JSONResponse(status_code=422, content={"detail": exc.errors()})
