"""Data-access repository classes abstracting database persistence.

Encapsulates CRUD operations for screening results and job descriptions,
decoupling the service layer from SQLAlchemy specifics.
"""

from .jd_repository import JDRepository
from .resume_repository import ResumeRepository

__all__ = ["JDRepository", "ResumeRepository"]
