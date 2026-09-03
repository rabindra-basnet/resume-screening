"""Unit tests for the base agent and the evaluator agent."""

from __future__ import annotations

import pytest
from app.agents.base import BaseAgent, StructuredOutputError
from app.agents.evaluator import EvaluatorAgent
from app.agents.resume_extractor import ResumeExtractorAgent
from app.models.candidate import CandidateProfile
from app.models.job_description import JobDescription
from pydantic import BaseModel


class _FakeClient:
    """A minimal fake LLM client returning canned responses."""

    def __init__(self, response: str) -> None:
        """Store the response the fake client should return."""
        self.response = response

    def complete(self, system_prompt: str, user_prompt: str, **kwargs: str) -> str:
        """Return the canned response, ignoring prompts."""
        return self.response


class _SampleModel(BaseModel):
    """A concrete model for exercising the base-agent parser."""

    status: str


class _PassthroughModel(BaseAgent[_SampleModel]):
    """Concrete agent subclass exposing the parsing helpers for testing."""

    response_model = _SampleModel

    def run(self, prompt: str, **kwargs: str) -> _SampleModel:
        """Parse a raw string through the base-agent response model."""
        return self.parse_response(prompt)


def test_parse_valid_json() -> None:
    """Valid JSON parses into the configured model."""
    agent = _PassthroughModel(client=_FakeClient(""))
    parsed = agent.parse_response('{"status": "ok"}')
    assert parsed.status == "ok"


def test_parse_invalid_json_raises() -> None:
    """Malformed JSON raises StructuredOutputError."""
    agent = _PassthroughModel(client=_FakeClient(""))
    with pytest.raises(StructuredOutputError):
        agent.parse_response("not json {{{")


def test_resume_extractor_validates_model() -> None:
    """Resume extraction parses and validates into CandidateProfile."""
    response = (
        '{"name": "Jane", "email": "jane@example.com", '
        '"work_experience_years": 5, "skills": ["Python"]}'
    )
    agent = ResumeExtractorAgent(client=_FakeClient(response))
    profile = agent.run("Some resume text")
    assert isinstance(profile, CandidateProfile)
    assert profile.name == "Jane"
    assert profile.skills == ["Python"]


def test_evaluator_overlays_deterministic_skill_match(sample_candidate, sample_job) -> None:
    """The evaluator overwrites skill fields with deterministic computation."""
    response = (
        '{"candidate_status": "selected", "reason": "Good fit", '
        '"skill_match_percentage": 99, "matched_skills": [], "missing_skills": []}'
    )
    agent = EvaluatorAgent(client=_FakeClient(response))
    result = agent.run(sample_candidate, sample_job)
    # 4 required skills, candidate has the first 4 => 100%
    assert result.skill_match_percentage == 100.0
    assert "Python" in result.matched_skills
    assert result.reason == "Good fit"


def test_evaluator_preserves_weak_skills_scoped_to_missing(
    sample_candidate: CandidateProfile, sample_job: JobDescription
) -> None:
    """Weak skills are kept only when they are among the missing required skills."""
    response = (
        '{"candidate_status": "selected", "reason": "Good fit", '
        '"matched_skills": [], "missing_skills": [], '
        '"weak_skills": ["FastAPI", "NotARequiredSkill"]}'
    )
    agent = EvaluatorAgent(client=_FakeClient(response))
    result = agent.run(sample_candidate, sample_job)
    # sample_job requires Python, FastAPI, SQLAlchemy, PostgreSQL.
    # sample_candidate weak list only overlaps with missing scope; all required
    # skills are matched, so no missing entries remain -> weak_skills empty.
    assert result.weak_skills == []
