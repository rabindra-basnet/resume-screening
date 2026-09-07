"""Six resume review agents for CV analysis and improvement.

To minimise token spend, review agents consume a compact structured context
(a :class:`CandidateProfile` extracted once) rather than the full raw resume
text. The raw text is only included when a task genuinely needs it (e.g. the
bullet re-writer must see the original bullet lines). This keeps each review
call small and shares the parsed profile across all agents.
"""

from __future__ import annotations

from app.models.candidate import CandidateProfile
from app.models.resume_review import (
    ATSOptimizationResult,
    BrutalReviewResult,
    BulletPointResult,
    FinalPolishResult,
    IndustryToneResult,
)
from app.prompts.resume_review import (
    ATS_OPTIMIZER,
    BRUTAL_HONEST_REVIEW,
    BULLET_POINT_TRANSFORMER,
    FINAL_POLISH,
    INDUSTRY_TONE_MATCH,
)

from .base import BaseAgent


def _compact_profile(candidate: CandidateProfile | None) -> str:
    """Return a compact JSON serialization of a candidate profile.

    Args:
        candidate: The parsed candidate profile, or ``None``.

    Returns:
        A compact JSON string (or empty if no profile available).
    """
    if candidate is None:
        return "(no structured profile available)"
    return candidate.model_dump_json(exclude_none=True)


class BrutalReviewAgent(BaseAgent[BrutalReviewResult]):
    """Simulate a senior hiring manager's unfiltered first-impression critique."""

    response_model = BrutalReviewResult

    def run(
        self,
        resume_text: str = "",
        candidate: CandidateProfile | None = None,
        *,
        industry: str = "",
        **kwargs: str,
    ) -> BrutalReviewResult:
        """Run the brutal honest review on a resume.

        Uses the compact candidate profile as the primary context; the raw text
        is only appended if provided and the profile is absent.

        Args:
            resume_text: Optional raw text of the resume.
            candidate: Optional parsed candidate profile (compact context).
            industry: Optional industry hint.
            **kwargs: Optional completion overrides.

        Returns:
            A validated :class:`BrutalReviewResult`.
        """
        industry_context = (
            f"Industry context: {industry}"
            if industry
            else "No specific industry given."
        )
        context = _compact_profile(candidate)
        if not context or context == "(no structured profile available)":
            context = resume_text or context
        user_prompt = BRUTAL_HONEST_REVIEW.format(
            candidate_context=context,
            industry_context=industry_context,
        )
        return self._complete_and_parse(user_prompt, **kwargs)


class ATSOptimizerAgent(BaseAgent[ATSOptimizationResult]):
    """Compare a candidate against a job description for ATS keyword gaps."""

    response_model = ATSOptimizationResult

    def run(
        self,
        candidate: CandidateProfile,
        job_description: str,
        **kwargs: str,
    ) -> ATSOptimizationResult:
        """Run ATS optimisation analysis.

        Uses a single shared context with the job description, minimising the
        per-call resume payload.

        Args:
            candidate: The parsed candidate profile (compact).
            job_description: Raw text of the target job description.
            **kwargs: Optional completion overrides.

        Returns:
            A validated :class:`ATSOptimizationResult`.
        """
        user_prompt = ATS_OPTIMIZER.format(
            candidate_context=_compact_profile(candidate),
            job_description=job_description,
        )
        return self._complete_and_parse(user_prompt, **kwargs)


class BulletPointTransformerAgent(BaseAgent[BulletPointResult]):
    """Rewrite resume bullets using Action Verb + Task + Measurable Result.

    This agent MUST see the original bullet lines, so it receives the raw text.
    """

    response_model = BulletPointResult

    def run(self, resume_text: str, **kwargs: str) -> BulletPointResult:
        """Run bullet-point transformation.

        Args:
            resume_text: Raw text extracted from the resume.
            **kwargs: Optional completion overrides.

        Returns:
            A validated :class:`BulletPointResult`.
        """
        user_prompt = BULLET_POINT_TRANSFORMER.format(resume_text=resume_text)
        return self._complete_and_parse(user_prompt, **kwargs)


class IndustryToneMatchAgent(BaseAgent[IndustryToneResult]):
    """Rewrite resume summary and skills to match an industry's tone.

    The industry is free-form text (not tied to any company list), keeping the
    product generic across all targets.
    """

    response_model = IndustryToneResult

    def run(
        self,
        candidate: CandidateProfile,
        industry: str,
        **kwargs: str,
    ) -> IndustryToneResult:
        """Run industry tone matching.

        Args:
            candidate: The parsed candidate profile.
            industry: The target industry (free-form generic string).
            **kwargs: Optional completion overrides.

        Returns:
            A validated :class:`IndustryToneResult`.
        """
        user_prompt = INDUSTRY_TONE_MATCH.format(
            candidate_context=_compact_profile(candidate),
            industry=industry or "general",
        )
        return self._complete_and_parse(user_prompt, **kwargs)


class FinalPolishAgent(BaseAgent[FinalPolishResult]):
    """Audit a resume for tense, cliches, and generic language."""

    response_model = FinalPolishResult

    def run(
        self,
        resume_text: str = "",
        candidate: CandidateProfile | None = None,
        **kwargs: str,
    ) -> FinalPolishResult:
        """Run the final polish audit.

        Prefers the compact candidate context to save tokens, but accepts raw
        text when a full-line audit is needed.

        Args:
            resume_text: Optional raw text.
            candidate: Optional compact candidate profile.
            **kwargs: Optional completion overrides.

        Returns:
            A validated :class:`FinalPolishResult`.
        """
        context = _compact_profile(candidate)
        if not context or context == "(no structured profile available)":
            context = resume_text or context
        user_prompt = FINAL_POLISH.format(candidate_context=context)
        return self._complete_and_parse(user_prompt, **kwargs)
