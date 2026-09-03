"""External job posting API endpoints for the v1 API.

Provides CRUD endpoints for job listings collected from external platforms
(LinkedIn, Indeed, etc.). This is the data-collection surface used by future
job scraper tools and the source for direct application from the app.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.database.schema import ExternalJobModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["external-jobs"])


@router.post("/external-jobs", summary="Ingest external job postings")
async def ingest_jobs(
    payload: dict,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Ingest one or more job postings collected by a scraper.

    Deduplicates by (platform, external_id) — a repeated posting updates the
    existing row rather than creating a duplicate.

    Args:
        payload: A dict with a ``jobs`` key containing a list of job dicts.
        session: The async database session.

    Returns:
        A dict with counts of created and updated rows.

    Raises:
        HTTPException: If the payload is malformed.
    """
    jobs = payload.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise HTTPException(status_code=422, detail="Expected payload with a non-empty 'jobs' list")

    created = 0
    updated = 0
    for raw in jobs:
        if not isinstance(raw, dict):
            raise HTTPException(status_code=422, detail="Each job must be an object")
        platform = str(raw.get("platform", "linkedin"))
        external_id = str(raw.get("external_id", ""))

        stmt = select(ExternalJobModel).where(
            ExternalJobModel.platform == platform,
            ExternalJobModel.external_id == external_id,
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()

        fields = {
            "title": raw.get("title", ""),
            "company": raw.get("company", ""),
            "location": raw.get("location", ""),
            "remote": raw.get("remote"),
            "url": raw.get("url", ""),
            "description": raw.get("description", ""),
            "salary_min": raw.get("salary_min"),
            "salary_max": raw.get("salary_max"),
            "currency": raw.get("currency", "USD"),
            "skills": raw.get("skills", []),
        }

        if existing:
            for key, value in fields.items():
                if value is not None:
                    setattr(existing, key, value)
            updated += 1
        else:
            session.add(ExternalJobModel(platform=platform, external_id=external_id, **fields))
            created += 1

    await session.commit()
    return {"created": created, "updated": updated, "total": created + updated}


@router.get("/external-jobs", summary="List external job postings")
async def list_jobs(
    session: Annotated[AsyncSession, Depends(get_session)],
    platform: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
) -> dict:
    """Return stored external job postings, optionally filtered by platform.

    Args:
        session: The async database session.
        platform: Optional platform slug to filter by.
        limit: Maximum number of rows to return.

    Returns:
        A dict with the list of job postings.
    """
    stmt = select(ExternalJobModel).order_by(ExternalJobModel.created_at.desc()).limit(limit)
    if platform:
        stmt = stmt.where(ExternalJobModel.platform == platform)
    rows = (await session.execute(stmt)).scalars().all()

    jobs = [
        {
            "id": r.id,
            "platform": r.platform,
            "external_id": r.external_id,
            "title": r.title,
            "company": r.company,
            "location": r.location,
            "remote": r.remote,
            "url": r.url,
            "description": r.description,
            "salary_min": r.salary_min,
            "salary_max": r.salary_max,
            "currency": r.currency,
            "skills": r.skills,
            "applied": r.applied,
            "posted_at": r.posted_at.isoformat() if r.posted_at else None,
        }
        for r in rows
    ]
    return {"jobs": jobs, "count": len(jobs)}
