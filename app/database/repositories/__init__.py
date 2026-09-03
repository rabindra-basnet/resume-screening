"""Data-access repository classes abstracting database persistence.

Encapsulates CRUD operations for screening results and job descriptions,
decoupling the service layer from SQLAlchemy specifics.
"""

from .jd_repository import JDRepository
from .learning_repository import LearningRepository
from .provider_repository import ProviderRepository
from .resume_repository import ResumeRepository

__all__ = ["JDRepository", "LearningRepository", "ProviderRepository", "ResumeRepository"]
