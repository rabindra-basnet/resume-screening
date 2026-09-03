"""Versioned (v1) API route modules."""

from .external_jobs import router as external_jobs_router
from .health import router as health_router
from .job_descriptions import router as jd_router
from .learning import router as learning_router
from .providers import router as providers_router
from .screening import router as screening_router

__all__ = [
    "health_router",
    "jd_router",
    "providers_router",
    "screening_router",
    "learning_router",
    "external_jobs_router",
]
