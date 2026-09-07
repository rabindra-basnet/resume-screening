"""Agent that decides whether a resume is ready to apply for a job."""

from __future__ import annotations

from app.models.resume_workspace import ApplyDecision
from app.prompts.apply_readiness import APPLY_READINESS

from .base import BaseAgent


class ApplyReadinessAgent(BaseAgent[ApplyDecision]):
    """Assess whether a polished resume is ready to submit for a job.

    Considers the resume content, the target job description, and a summary of
    the chat session to decide on the application's readiness.
    """

    response_model = ApplyDecision

    def run(
        self,
        resume_text: str,
        *,
        job_description: str = "",
        chat_summary: str = "",
        **kwargs: str,
    ) -> ApplyDecision:
        """Run readiness assessment.

        Args:
            resume_text: Final (edited) resume text.
            job_description: Optional target job description.
            chat_summary: Optional summary of the iteration chat.
            **kwargs: Optional completion overrides.

        Returns:
            A validated :class:`ApplyDecision`.
        """
        user_prompt = APPLY_READINESS.format(
            job_description=job_description or "(none provided)",
            resume_text=resume_text,
            chat_summary=chat_summary or "(no chat sessions)",
        )
        return self._complete_and_parse(user_prompt, **kwargs)
