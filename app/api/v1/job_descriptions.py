"""Job-description management endpoints for the v1 API."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.database.repositories import JDRepository
from app.models import JobDescription, JobDescriptionCreate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/job-descriptions", tags=["job-descriptions"])


@router.post("", response_model=JobDescription, status_code=201, summary="Create a job description")
async def create_job_description(
    payload: JobDescriptionCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> JobDescription:
    """Create and persist a new job description.

    Args:
        payload: The job-description title and raw text.
        session: The injected async database session.

    Returns:
        The persisted :class:`JobDescription`.
    """
    repo = JDRepository(session)
    job = JobDescription(title=payload.title, raw_text=payload.raw_text)
    row = await repo.upsert(job)
    return JDRepository._from_model(row)


@router.get("/{jd_id}", response_model=JobDescription, summary="Get a job description")
async def get_job_description(
    jd_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> JobDescription:
    """Fetch a stored job description by id.

    Args:
        jd_id: The job-description primary key.
        session: The injected async database session.

    Returns:
        The matching :class:`JobDescription`.

    Raises:
        HTTPException: If the job description is not found.
    """
    repo = JDRepository(session)
    row = await repo.get(jd_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Job description not found")
    return JDRepository._from_model(row)
