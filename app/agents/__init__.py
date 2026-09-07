"""Agent orchestration for the screening pipeline.

Defines the base agent contract and concrete agent implementations that wrap
OpenAI-compatible LLM providers (via LiteLLM) to extract structured data and
evaluate candidates.
"""

from .apply_readiness import ApplyReadinessAgent
from .base import BaseAgent, StructuredOutputError
from .evaluator import EvaluatorAgent
from .jd_extractor import JDGeneratorAgent
from .learning_resource_agent import LearningResourceAgent, LearningResourcesResponse
from .llm_client import LLMClient, LLMError, LLMTimeoutError
from .orchestrator import AgentOrchestrator
from .resume_chat import ResumeChatAgent
from .resume_extractor import ResumeExtractorAgent
from .resume_review import (
    ATSOptimizerAgent,
    BrutalReviewAgent,
    BulletPointTransformerAgent,
    FinalPolishAgent,
    IndustryToneMatchAgent,
)

__all__ = [
    "BaseAgent",
    "StructuredOutputError",
    "LLMClient",
    "LLMError",
    "LLMTimeoutError",
    "ResumeExtractorAgent",
    "JDGeneratorAgent",
    "EvaluatorAgent",
    "LearningResourceAgent",
    "LearningResourcesResponse",
    "AgentOrchestrator",
    "BrutalReviewAgent",
    "ATSOptimizerAgent",
    "BulletPointTransformerAgent",
    "IndustryToneMatchAgent",
    "FinalPolishAgent",
    "ApplyReadinessAgent",
    "ResumeChatAgent",
]
