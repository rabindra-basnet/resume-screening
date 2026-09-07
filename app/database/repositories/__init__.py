"""Data-access repository classes abstracting database persistence.

Encapsulates CRUD operations for screening results and job descriptions,
decoupling the service layer from SQLAlchemy specifics.
"""

from .jd_repository import JDRepository
from .job_application_repository import JobApplicationRepository
from .learning_repository import LearningRepository
from .provider_repository import ProviderRepository
from .resume_chat_session_repository import ResumeChatSessionRepository
from .resume_edit_session_repository import ResumeEditSessionRepository
from .resume_repository import ResumeRepository
from .resume_review_repository import ResumeReviewRepository
from .user_repository import UserRepository

__all__ = [
    "JDRepository",
    "LearningRepository",
    "ProviderRepository",
    "ResumeRepository",
    "UserRepository",
    "ResumeReviewRepository",
    "ResumeEditSessionRepository",
    "ResumeChatSessionRepository",
    "JobApplicationRepository",
]
