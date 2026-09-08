"""Resume review endpoints for the v1 API."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.deps import get_current_user_or_none, get_resume_review_service
from app.config.constants import ALLOWED_EXTENSIONS, MAX_UPLOAD_BYTES
from app.database.schema import UserModel
from app.services import ResumeReviewService
from app.tools import DocumentParsingError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["resume-review"])


@router.post("/resume-review", summary="Run a resume review agent")
async def run_resume_review(
    user: UserModel | None = Depends(get_current_user_or_none),
    service: ResumeReviewService = Depends(get_resume_review_service),
    resume: UploadFile | None = File(default=None),
    resume_text: str = Form(default=""),
    review_type: str = Form(default="full"),
    industry: str = Form(default=""),
    job_description: str = Form(default=""),
    model_override: str | None = Form(default=None),
) -> dict:
    """Run one (or all) of the resume review agents on an uploaded resume.

    Args:
        user: Optional authenticated user.
        resume: The resume file (PDF or DOCX) to review.
        resume_text: Optional inline resume text (used instead of a file).
        review_type: Which review to run (full/brutal/ats/bullets/tone/polish).
        industry: Optional free-form target industry (tone matching).
        job_description: Optional JD text (ATS optimisation).
        model_override: Optional LLM model override.
        service: The injected resume review service.

    Returns:
        A dict with the review results and metadata.

    Raises:
        HTTPException: For validation errors or document parsing failures.
    """
    if not resume_text.strip() and resume is None:
        raise HTTPException(status_code=400, detail="resume file or resume_text is required")

    content: bytes | None = None
    filename = ""
    if resume is not None:
        filename = (resume.filename or "").strip()
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        if f".{ext}" not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail="Only PDF (.pdf) and Word (.docx) files are accepted",
            )
        content = await resume.read()
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="File exceeds the 10MB limit")

    if review_type not in ("full", "brutal", "ats", "bullets", "tone", "polish"):
        raise HTTPException(
            status_code=422,
            detail="review_type must be one of full/brutal/ats/bullets/tone/polish",
        )
    if review_type == "ats" and not job_description:
        raise HTTPException(
            status_code=422, detail="job_description is required for ATS review"
        )

    try:
        return await service.run_review(
            content,
            resume_text=resume_text,
            resume_filename=filename,
            review_type=review_type,
            industry=industry,
            job_description=job_description,
            model_override=model_override,
            user_id=user.id if user else None,
        )
    except DocumentParsingError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
