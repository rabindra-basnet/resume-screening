"""Health-check endpoint for the v1 API."""

from __future__ import annotations

from fastapi import APIRouter

from app.models import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Service health check")
async def health() -> HealthResponse:
    """Return the service health status.

    Returns:
        A :class:`HealthResponse` indicating the service is operational.
    """
    return HealthResponse(status="ok", app="agentic-resume-screening", database="ok")
