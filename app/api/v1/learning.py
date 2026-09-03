"""Learning resources API endpoints for the v1 API.

Provides retrieval endpoints for the learning plans persisted during screening,
backing the /admin/learning page.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_learning_repo
from app.database.repositories import LearningRepository

logger = logging.getLogger(__name__)

router = APIRouter(tags=["learning"])


@router.get("/learning", summary="List recent learning resources")
async def list_learning_resources(
    repo: Annotated[LearningRepository, Depends(get_learning_repo)],
    limit: int = 100,
) -> dict:
    """Return the most recent learning resources across all screenings.

    Args:
        repo: The injected learning repository.
        limit: Maximum number of resources to return.

    Returns:
        A dict with the list of persisted learning resources.
    """
    rows = await repo.list_all(limit=limit)
    resources = [
        {
            "id": r.id,
            "screening_id": r.screening_id,
            "skill": r.skill,
            "title": r.title,
            "url": r.url,
            "resource_type": r.resource_type,
            "provider": r.provider,
            "description": r.description,
            "estimated_hours": r.estimated_hours,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
    return {"resources": resources}


@router.get("/learning/{screening_id}", summary="List resources for a screening")
async def list_screening_resources(
    screening_id: str,
    repo: Annotated[LearningRepository, Depends(get_learning_repo)],
) -> dict:
    """Return learning resources associated with a specific screening.

    Args:
        screening_id: The screening result id.
        repo: The injected learning repository.

    Returns:
        A dict with the list of learning resources for the screening.

    Raises:
        HTTPException: If no screening matches or has resources.
    """
    rows = await repo.list_by_screening(screening_id)
    resources = [
        {
            "id": r.id,
            "screening_id": r.screening_id,
            "skill": r.skill,
            "title": r.title,
            "url": r.url,
            "resource_type": r.resource_type,
            "provider": r.provider,
            "description": r.description,
            "estimated_hours": r.estimated_hours,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
    return {"resources": resources, "count": len(resources)}
