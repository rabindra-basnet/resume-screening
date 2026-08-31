"""Agent that extracts structured job-description requirements from text."""

from __future__ import annotations

from app.models.job_description import JobDescription
from app.prompts import EXTRACT_JD_DETAILS

from .base import BaseAgent


class JDGeneratorAgent(BaseAgent[JobDescription]):
    """Extract structured :class:`JobDescription` requirements from raw text.

    Parses a job posting into title, experience range, and required skills.
    """

    response_model = JobDescription

    def run(self, text: str, **kwargs: str) -> JobDescription:
        """Extract job description requirements from text.

        Args:
            text: Raw text content of the job description.
            **kwargs: Optional completion overrides (e.g. model, temperature).

        Returns:
            A validated :class:`JobDescription`.
        """
        user_prompt = EXTRACT_JD_DETAILS.format(jd_text=text)
        return self._complete_and_parse(user_prompt, **kwargs)
