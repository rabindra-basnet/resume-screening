"""Prompt templates used by the screening agents.

Templates are defined as module-level constants and populated at call time with
the relevant input text. Each agent owns exactly one template to keep prompts
colocated with their consuming logic.
"""

from .apply_readiness import APPLY_READINESS
from .evaluation import CANDIDATE_EVALUATION
from .jd_extraction import EXTRACT_JD_DETAILS
from .learning import LEARNING_RESOURCES
from .resume_chat import RESUME_CHAT, build_lined_resume
from .resume_extraction import EXTRACT_CANDIDATE_DETAILS
from .resume_review import (
    ATS_OPTIMIZER,
    BRUTAL_HONEST_REVIEW,
    BULLET_POINT_TRANSFORMER,
    FINAL_POLISH,
    INDUSTRY_TONE_MATCH,
)

__all__ = [
    "EXTRACT_CANDIDATE_DETAILS",
    "EXTRACT_JD_DETAILS",
    "CANDIDATE_EVALUATION",
    "LEARNING_RESOURCES",
    "BRUTAL_HONEST_REVIEW",
    "ATS_OPTIMIZER",
    "BULLET_POINT_TRANSFORMER",
    "INDUSTRY_TONE_MATCH",
    "FINAL_POLISH",
    "RESUME_CHAT",
    "build_lined_resume",
    "APPLY_READINESS",
]
