"""Agent that evaluates a candidate profile against a job description."""

from __future__ import annotations

from app.models.candidate import CandidateProfile
from app.models.evaluation import EvaluationResult
from app.models.job_description import JobDescription
from app.prompts import CANDIDATE_EVALUATION
from app.tools.skill_matcher import calculate_skill_match

from .base import BaseAgent


class EvaluatorAgent(BaseAgent[EvaluationResult]):
    """Evaluate a candidate against a job description and produce a verdict.

    The agent asks an LLM for a reasoned evaluation, then overlays a
    deterministic skill-match computation as a guardrail against hallucinated
    or inconsistent matching.
    """

    response_model = EvaluationResult

    def run(
        self,
        candidate: CandidateProfile,
        job: JobDescription,
        **kwargs: str,
    ) -> EvaluationResult:
        """Evaluate a candidate profile against a job description.

        Args:
            candidate: The extracted candidate profile.
            job: The structured job description.
            **kwargs: Optional completion overrides (e.g. model, temperature).

        Returns:
            A validated :class:`EvaluationResult`.

        Raises:
            StructuredOutputError: If the LLM response cannot be parsed.
        """
        resume_json = candidate.model_dump_json()
        jd_json = job.model_dump_json(exclude_none=True)
        user_prompt = CANDIDATE_EVALUATION.format(resume_json=resume_json, jd_json=jd_json)
        result = self._complete_and_parse(user_prompt, **kwargs)
        return self._overlay_skill_match(result, candidate, job)

    def _overlay_skill_match(
        self,
        result: EvaluationResult,
        candidate: CandidateProfile,
        job: JobDescription,
    ) -> EvaluationResult:
        """Overwrite result skill fields with deterministic computation.

        Args:
            result: The LLM-produced evaluation result.
            candidate: The candidate profile used for skill matching.
            job: The job description used for required skills.

        Returns:
            The evaluation result with deterministic matched/missing/percentage
            fields populated.
        """
        matched, missing, percentage = calculate_skill_match(candidate.skills, job.skills)
        result.matched_skills = matched
        result.missing_skills = missing
        result.skill_match_percentage = percentage
        return result
