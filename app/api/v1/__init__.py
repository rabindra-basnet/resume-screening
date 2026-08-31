"""Versioned (v1) API route modules."""

from .health import router as health_router
from .job_descriptions import router as jd_router
from .screening import router as screening_router

__all__ = ["health_router", "jd_router", "screening_router"]
