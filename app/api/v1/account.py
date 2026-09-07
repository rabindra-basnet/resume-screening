"""Account dashboard API — documents list and download."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUserDep
from app.database.repositories.resume_repository import ResumeRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/account", tags=["account"])


@router.get("/documents")
async def list_documents(
    ctx: CurrentUserDep,
) -> list[dict]:
    """Return the current user's screening results (documents).

    Returns:
        A list of screening result dicts with blob URLs and metadata.
    """
    repo = ResumeRepository(ctx.session)
    rows = await repo.list_by_user(ctx.user_id, limit=100)
    return [
        {
            "id": row.id,
            "resume_filename": row.resume_filename,
            "resume_blob_url": row.resume_blob_url,
            "status": row.status,
            "skill_match_percentage": row.skill_match_percentage,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]


@router.get("/documents/{screening_id}")
async def get_document(
    screening_id: str,
    ctx: CurrentUserDep,
) -> dict:
    """Return a single screening result if owned by the current user.

    Raises:
        HTTPException: 404 if not found or not owned.
    """
    repo = ResumeRepository(ctx.session)
    row = await repo.get(screening_id)
    if row is None or row.user_id != ctx.user_id:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": row.id,
        "resume_filename": row.resume_filename,
        "resume_blob_url": row.resume_blob_url,
        "resume_text": row.resume_text,
        "candidate_profile": row.candidate_profile,
        "evaluation": row.evaluation,
        "status": row.status,
        "skill_match_percentage": row.skill_match_percentage,
        "llm_model_used": row.llm_model_used,
        "processing_time_ms": row.processing_time_ms,
        "jd_id": row.jd_id,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }
