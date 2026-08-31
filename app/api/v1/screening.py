"""Screening endpoint for the v1 API."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_screening_service, get_session
from app.config.constants import MAX_UPLOAD_BYTES
from app.services import ScreeningService
from app.tools import PDFParsingError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["screening"])


@router.post("/screening", summary="Screen a resume against a job description")
async def screen_resume(
    resume: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    service: ScreeningService = Depends(get_screening_service),
    jd_id: str | None = Form(default=None),
    job_description: str | None = Form(default=None),
    model_override: str | None = Form(default=None),
) -> dict:
    """Run a full resume screening against a stored or inline job description.

    Args:
        resume: The resume PDF file to screen.
        jd_id: Optional id of a stored job description.
        job_description: Optional inline job description text.
        model_override: Optional LLM model override.
        session: Injected async database session (unused directly).
        service: The injected screening service.

    Returns:
        A dict containing the candidate profile, evaluation, and metadata.

    Raises:
        HTTPException: For validation errors, missing job context, or a
            PDF parsing failure.
    """
    if not resume.filename or not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    content = await resume.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 10MB limit")

    if not jd_id and not job_description:
        raise HTTPException(status_code=422, detail="Either jd_id or job_description is required")

    try:
        return await service.run_screening(
            content,
            resume_filename=resume.filename,
            jd_id=jd_id,
            job_description=job_description,
            model_override=model_override,
        )
    except PDFParsingError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
