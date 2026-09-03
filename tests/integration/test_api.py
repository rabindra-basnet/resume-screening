"""Integration test for the screening API with mocked LLM agents.

Uses a temporary SQLite database (from the session fixture) and overrides the
screening-service dependency with fake agents so the full HTTP flow is tested
without real LLM calls.
"""

from __future__ import annotations

import io

import httpx
import pytest
from app.agents.base import BaseAgent
from app.agents.evaluator import EvaluatorAgent
from app.agents.jd_extractor import JDGeneratorAgent
from app.agents.llm_client import LLMClient
from app.agents.orchestrator import AgentOrchestrator
from app.agents.resume_extractor import ResumeExtractorAgent
from app.main import create_app
from app.models.job_description import JobDescription
from app.services import ScreeningService
from fastapi import Depends
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_screening_service, get_session
from app.database.schema import UserModel


def _make_minimal_pdf(text: str = "Hello Resume") -> bytes:
    """Generate a valid single-page PDF containing ``text`` using pypdf."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_ref = writer._add_object(font)
    content = DecodedStreamObject()
    content.set_data(f"BT /F1 24 Tf 100 700 Td ({text}) Tj ET".encode())
    content_ref = writer._add_object(content)
    res = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})}
    )
    page[NameObject("/Resources")] = res
    page[NameObject("/Contents")] = content_ref
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


class _FakeLLMClient(LLMClient):
    """A fake LLM client returning canned structured responses."""

    def complete(self, system_prompt: str, user_prompt: str, **kwargs: str) -> str:
        """Return a canned JSON response based on the request."""
        if "candidate profile" in system_prompt.lower() or "resume" in user_prompt.lower():
            return (
                '{"name": "John Doe", "email": "john@example.com", '
                '"work_experience_years": 6, "skills": ["Python", "FastAPI", '
                '"SQLAlchemy", "PostgreSQL", "Docker", "CI/CD"]}'
            )
        return (
            '{"candidate_status": "selected", "reason": "Candidate matches.", '
            '"matched_skills": [], "missing_skills": [], '
            '"skill_match_percentage": 80, "experience_years": 6}'
        )


@pytest.fixture
async def client(db):
    """Build a test ASGI client with a screening service bound to fake agents."""
    app = create_app()

    def _build_fake_service(
        session: AsyncSession = Depends(get_session),
    ) -> ScreeningService:
        fake_client = _FakeLLMClient()
        resume_agent = ResumeExtractorAgent(client=fake_client)
        evaluator = EvaluatorAgent(client=fake_client)

        # JD generation uses the resume prompt route; build a minimal fake.
        class _FakeJD(BaseAgent):
            def run(self, text: str, **kwargs: str) -> JobDescription:
                return JobDescription(
                    title="Senior Python Engineer",
                    raw_text=text,
                    min_work_experience=5,
                    max_work_experience=8,
                    skills=["Python", "FastAPI", "SQLAlchemy", "PostgreSQL"],
                )

        jd_agent: JDGeneratorAgent = _FakeJD()  # type: ignore[assignment]
        orchestrator = AgentOrchestrator(
            resume_extractor=resume_agent, jd_extractor=jd_agent, evaluator=evaluator
        )
        return ScreeningService(session=session, orchestrator=orchestrator)

    app.dependency_overrides[get_session] = lambda: db.session()
    app.dependency_overrides[get_screening_service] = _build_fake_service

    # Mock authenticated user for screening tests.
    _fake_user = UserModel(
        id="test-user-id",
        email="test@example.com",
        name="Test User",
        avatar_url=None,
        google_id="fake-google-id",
    )
    app.dependency_overrides[get_current_user] = lambda: _fake_user

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_screening_flow(client) -> None:
    """A PDF upload returns a structured screening response."""
    files = {"resume": ("resume.pdf", io.BytesIO(_make_minimal_pdf()), "application/pdf")}
    data = {"job_description": "Senior Python Engineer requires Python and FastAPI."}

    response = await client.post("/api/v1/screening", files=files, data=data)
    assert response.status_code == 200
    payload = response.json()
    assert "screening_id" in payload
    assert payload["evaluation"]["candidate_status"] == "selected"
    assert "candidate" in payload


@pytest.mark.asyncio
async def test_screening_rejects_non_pdf(client, valid_resume_text) -> None:
    """Non-PDF uploads are rejected with a 400."""
    files = {
        "resume": (
            "resume.txt",
            io.BytesIO(valid_resume_text.encode("utf-8")),
            "text/plain",
        )
    }
    data = {"job_description": "Some job"}
    response = await client.post("/api/v1/screening", files=files, data=data)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_screening_requires_context(client) -> None:
    """Screening without a JD raises a 422."""
    files = {"resume": ("resume.pdf", io.BytesIO(b"%PDF fake"), "application/pdf")}
    response = await client.post("/api/v1/screening", files=files, data={})
    assert response.status_code == 422
