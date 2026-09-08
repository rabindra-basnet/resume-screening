"""Versioned (v1) API route modules."""

from .account import router as account_router
from .auth import router as auth_router
from .external_jobs import router as external_jobs_router
from .health import router as health_router
from .job_descriptions import router as jd_router
from .learning import router as learning_router
from .llm import router as llm_router
from .providers import router as providers_router
from .resume_chat import router as resume_chat_router
from .resume_edit import router as resume_edit_router
from .resume_review import router as resume_review_router
from .screening import router as screening_router

__all__ = [
    "account_router",
    "auth_router",
    "health_router",
    "jd_router",
    "llm_router",
    "providers_router",
    "screening_router",
    "learning_router",
    "external_jobs_router",
    "resume_review_router",
    "resume_edit_router",
    "resume_chat_router",
]
