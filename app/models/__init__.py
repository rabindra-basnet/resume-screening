"""Pydantic data models representing domain entities and API contracts.

These models define the shared, validated contracts used across the API layer,
the LLM agents, and the database repositories. Enforcing structured types at
every boundary prevents malformed data from propagating through the pipeline.
"""

from .api import HealthResponse, ScreeningRequest, ScreeningResponse
from .candidate import CandidateProfile, Education, WorkExperience
from .evaluation import EvaluationResult, SkillMatch
from .job_description import JobDescription, JobDescriptionCreate

__all__ = [
    "CandidateProfile",
    "Education",
    "WorkExperience",
    "JobDescription",
    "JobDescriptionCreate",
    "EvaluationResult",
    "SkillMatch",
    "ScreeningRequest",
    "ScreeningResponse",
    "HealthResponse",
]
