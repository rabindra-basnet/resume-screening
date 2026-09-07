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
from .resume_review import (
    ATSOptimizerAgent,
    BrutalReviewAgent,
    BulletPointTransformerAgent,
    FinalPolishAgent,
    IndustryToneMatchAgent,
)

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Coordinate the resume screening and review agent pipelines.

    Args:
        resume_extractor: Agent responsible for extracting candidate profiles.
        jd_extractor: Agent responsible for parsing job descriptions.
        evaluator: Agent responsible for scoring the candidate against the JD.
        brutal_review: Agent for unfiltered hiring-manager critique.
        ats_optimizer: Agent for ATS keyword-gap analysis.
        bullet_transformer: Agent for rewriting bullets with Action+Task+Result.
        industry_tone: Agent for industry-specific tone matching.
        final_polish: Agent for tense/cliche/genericity audit.
    """

    def __init__(
        self,
        resume_extractor: ResumeExtractorAgent | None = None,
        jd_extractor: JDGeneratorAgent | None = None,
        evaluator: EvaluatorAgent | None = None,
        brutal_review: BrutalReviewAgent | None = None,
        ats_optimizer: ATSOptimizerAgent | None = None,
        bullet_transformer: BulletPointTransformerAgent | None = None,
        industry_tone: IndustryToneMatchAgent | None = None,
        final_polish: FinalPolishAgent | None = None,
    ) -> None:
        """Initialize the orchestrator with all pipeline agents."""
        self.resume_extractor = resume_extractor or ResumeExtractorAgent()
        self.jd_extractor = jd_extractor or JDGeneratorAgent()
        self.evaluator = evaluator or EvaluatorAgent()
        self.brutal_review = brutal_review or BrutalReviewAgent()
        self.ats_optimizer = ats_optimizer or ATSOptimizerAgent()
        self.bullet_transformer = bullet_transformer or BulletPointTransformerAgent()
        self.industry_tone = industry_tone or IndustryToneMatchAgent()
        self.final_polish = final_polish or FinalPolishAgent()

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

    def review_resume(
        self,
        resume_text: str,
        *,
        industry: str = "",
        job_description: str = "",
        review_type: str = "full",
    ) -> dict:
        """Run resume review agents for improvement feedback.

        To reduce token spend, the resume is parsed once into a compact
        :class:`CandidateProfile` (via the resume extractor) and that compact
        context is shared across the review agents. Only the bullet-point
        transformer needs the full raw text (to rewrite each line).

        Args:
            resume_text: Raw text extracted from the resume.
            industry: Optional free-form target industry (generic, no company
                assumptions).
            job_description: Optional JD text for ATS optimisation.
            review_type: Which review to run. One of
                ``full``, ``brutal``, ``ats``, ``bullets``, ``tone``, ``polish``.

        Returns:
            A dict with the requested review results (keys may be ``None``
            when the corresponding agent was not run).
        """
        result: dict = {
            "brutal_review": None,
            "ats_optimization": None,
            "bullet_points": None,
            "industry_tone": None,
            "final_polish": None,
        }

        # Parse once and share the compact profile to save tokens across the
        # review agents that consume structured context.
        candidate = self.resume_extractor.run(resume_text)

        if review_type in ("full", "brutal"):
            result["brutal_review"] = self.brutal_review.run(
                candidate=candidate, industry=industry
            ).model_dump(mode="json")
            logger.info("Brutal review complete")

        if review_type in ("full", "ats") and job_description:
            result["ats_optimization"] = self.ats_optimizer.run(
                candidate=candidate, job_description=job_description
            ).model_dump(mode="json")
            logger.info("ATS optimisation complete")

        if review_type in ("full", "bullets"):
            result["bullet_points"] = self.bullet_transformer.run(
                resume_text
            ).model_dump(mode="json")
            logger.info("Bullet transformation complete")

        if review_type in ("full", "tone") and industry:
            result["industry_tone"] = self.industry_tone.run(
                candidate=candidate, industry=industry
            ).model_dump(mode="json")
            logger.info("Industry tone match complete")

        if review_type in ("full", "polish"):
            result["final_polish"] = self.final_polish.run(
                candidate=candidate
            ).model_dump(mode="json")
            logger.info("Final polish complete")

        return result
