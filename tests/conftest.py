"""Shared pytest fixtures and configuration for the test suite."""

from __future__ import annotations

import sys
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

# Ensure the project root (parent of tests/) is importable.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.database import Base  # noqa: E402
from app.database.connection import Database  # noqa: E402
from app.models import CandidateProfile, JobDescription  # noqa: E402


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point config at throwaway credentials for the test run."""
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///")


@pytest.fixture
async def db() -> AsyncIterator[Database]:
    """Provide a fresh isolated SQLite engine with schema created.

    Creates a dedicated in-memory SQLite database per test to avoid the cached
    global connection singleton shared across the app.

    Yields:
        A configured :class:`Database` instance with tables created.
    """
    url = f"sqlite+aiosqlite:///{tempfile.mkdtemp()}/test.db"
    database = Database(url=url)
    # Import all models so metadata is complete.
    import app.database.schema  # noqa: F401

    async with database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield database
    await database.dispose()


@pytest.fixture
def valid_resume_text() -> str:
    """Return a minimal realistic resume text for tests.

    Returns:
        A short resume string containing skills and experience clues.
    """
    return (
        "John Doe\njohn@example.com\nSenior Python Engineer with 6 years "
        "experience. Skills: Python, FastAPI, SQLAlchemy, PostgreSQL, Docker, "
        "CI/CD. Bachelor of Science in Computer Science."
    )


@pytest.fixture
def sample_job() -> JobDescription:
    """Return a structured sample job description for tests.

    Returns:
        A :class:`JobDescription` with Python and FastAPI as required skills.
    """
    return JobDescription(
        title="Senior Python Engineer",
        raw_text="Senior Python Engineer. Requires Python, FastAPI, SQLAlchemy.",
        min_work_experience=5,
        max_work_experience=8,
        skills=["Python", "FastAPI", "SQLAlchemy", "PostgreSQL"],
    )


@pytest.fixture
def sample_candidate() -> CandidateProfile:
    """Return a structured sample candidate profile for tests.

    Returns:
        A :class:`CandidateProfile` matching several of the sample JD skills.
    """
    return CandidateProfile(
        name="John Doe",
        email="john@example.com",
        work_experience_years=6,
        skills=["Python", "FastAPI", "SQLAlchemy", "PostgreSQL", "Docker"],
    )
