"""Prompt templates used by the screening agents.

Templates are defined as module-level constants and populated at call time with
the relevant input text. Each agent owns exactly one template to keep prompts
colocated with their consuming logic.
"""

from .evaluation import CANDIDATE_EVALUATION
from .jd_extraction import EXTRACT_JD_DETAILS
from .learning import LEARNING_RESOURCES
from .resume_extraction import EXTRACT_CANDIDATE_DETAILS

__all__ = [
    "EXTRACT_CANDIDATE_DETAILS",
    "EXTRACT_JD_DETAILS",
    "CANDIDATE_EVALUATION",
    "LEARNING_RESOURCES",
]
