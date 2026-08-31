"""Agent that extracts a structured candidate profile from resume text."""

from __future__ import annotations

from app.models.candidate import CandidateProfile
from app.prompts import EXTRACT_CANDIDATE_DETAILS

from .base import BaseAgent


class ResumeExtractorAgent(BaseAgent[CandidateProfile]):
    """Extract a structured :class:`CandidateProfile` from raw resume text.

    Uses an LLM to parse unstructured resume content into a typed model with
    education, skills, certifications, and work history.
    """

    response_model = CandidateProfile

    def run(self, resume_text: str, **kwargs: str) -> CandidateProfile:
        """Extract candidate profile from resume text.

        Args:
            resume_text: Raw text content extracted from the resume PDF.
            **kwargs: Optional completion overrides (e.g. model, temperature).

        Returns:
            A validated :class:`CandidateProfile`.
        """
        user_prompt = EXTRACT_CANDIDATE_DETAILS.format(resume_text=resume_text)
        return self._complete_and_parse(user_prompt, **kwargs)
