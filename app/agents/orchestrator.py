"""Sequential pipeline orchestrator that runs the screening agents.

Combines the resume extraction, job-description resolution, and evaluation
agents into a single callable workflow. Designed to be easily extended with
parallel stages (e.g. batched resume screening) without changing callers.
"""

from __future__ import annotations

import logging

from .evaluator import EvaluatorAgent
from .jd_extractor import JDGeneratorAgent
from .resume_extractor import ResumeExtractorAgent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Coordinate the resume screening agent pipeline.

    Args:
        resume_extractor: Agent responsible for extracting candidate profiles.
        jd_extractor: Agent responsible for parsing job descriptions.
        evaluator: Agent responsible for scoring the candidate against the JD.
    """

    def __init__(
        self,
        resume_extractor: ResumeExtractorAgent | None = None,
        jd_extractor: JDGeneratorAgent | None = None,
        evaluator: EvaluatorAgent | None = None,
    ) -> None:
        """Initialize the orchestrator with the three pipeline agents."""
        self.resume_extractor = resume_extractor or ResumeExtractorAgent()
        self.jd_extractor = jd_extractor or JDGeneratorAgent()
        self.evaluator = evaluator or EvaluatorAgent()

    def screen(self, resume_text: str, job_description: str) -> tuple:
        """Run the full screening pipeline for a single resume.

        Args:
            resume_text: Raw text extracted from the candidate's resume.
            job_description: Raw text content of the job description.

        Returns:
            A tuple of ``(candidate, job, evaluation)`` where ``candidate`` is
            the extracted :class:`CandidateProfile`, ``job`` is the parsed
            :class:`JobDescription`, and ``evaluation`` is the
            :class:`EvaluationResult`.

        Raises:
            app.agents.base.StructuredOutputError: If any agent returns
                unparseable output.
            app.agents.llm_client.LLMError: If an LLM call ultimately fails.
        """
        candidate = self.resume_extractor.run(resume_text)
        job = self.jd_extractor.run(job_description)
        evaluation = self.evaluator.run(candidate, job)
        logger.info(
            "Screening complete: status=%s match=%s%%",
            evaluation.candidate_status,
            evaluation.skill_match_percentage,
        )
        return candidate, job, evaluation
