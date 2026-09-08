"""Resume editing endpoints supporting undo/redo."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.deps import get_current_user_or_none, get_resume_edit_service
from app.config.constants import ALLOWED_EXTENSIONS, MAX_UPLOAD_BYTES
from app.database.schema import UserModel
from app.models.resume_workspace import (
    ResumeEditApplyRequest,
    ResumeEditApplyResponse,
    ResumeEditUndoResponse,
)
from app.services import EditConflictError, ResumeEditService
from app.tools import DocumentParsingError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["resume-edit"])


@router.post("/resume-edit/session", summary="Create a resume editing session")
async def create_edit_session(
    user: UserModel | None = Depends(get_current_user_or_none),
    service: ResumeEditService = Depends(get_resume_edit_service),
    resume: UploadFile | None = File(default=None),
    resume_text: str = Form(default=""),
) -> dict:
    """Upload a resume (or paste its text) and create an editable session.

    Either a ``resume`` file or a pasted ``resume_text`` must be supplied so the
    chat-box screening flow works without requiring a file upload.

    Args:
        user: Optional authenticated user.
        resume: The resume file (PDF or DOCX), when provided.
        resume_text: Raw resume text, when pasted instead of uploaded.
        service: The injected resume editing service.

    Returns:
        A dict with the editing session id and the initial content.

    Raises:
        HTTPException: For validation errors or document parsing failures.
    """
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

        from app.tools import DocumentParser

        try:
            resume_text = DocumentParser().extract_text(content, filename)
        except DocumentParsingError as exc:
            raise HTTPException(status_code=400, detail=exc.message) from exc
    elif not resume_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Either a resume file or resume_text is required",
        )

    session_id = await service.create_session(
        resume_text=resume_text.strip() or resume_text,
        user_id=user.id if user else None,
        resume_filename=resume.filename if resume else None,
    )
    return {"session_id": session_id, "content": resume_text}


@router.get("/resume-edit/session/{session_id}", summary="Get editing session content")
async def get_edit_session(
    session_id: str,
    user: UserModel | None = Depends(get_current_user_or_none),
    service: ResumeEditService = Depends(get_resume_edit_service),
) -> dict:
    """Return the current content of an editing session."""
    content = await service.get_content(session_id, user_id=user.id if user else None)
    if content is None:
        raise HTTPException(status_code=404, detail="Editing session not found")
    return {"session_id": session_id, "content": content}


@router.post(
    "/resume-edit/session/{session_id}/apply",
    response_model=ResumeEditApplyResponse,
    summary="Apply an edit with undo/redo",
)
async def apply_edit(
    session_id: str,
    payload: ResumeEditApplyRequest,
    user: UserModel | None = Depends(get_current_user_or_none),
    service: ResumeEditService = Depends(get_resume_edit_service),
) -> ResumeEditApplyResponse:
    """Apply a single line-based edit to the editing session."""
    try:
        return await service.apply_edit(
            session_id, payload.action, user_id=user.id if user else None
        )
    except EditConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    except KeyError:
        raise HTTPException(status_code=404, detail="Editing session not found") from None


@router.post(
    "/resume-edit/session/{session_id}/undo",
    response_model=ResumeEditUndoResponse,
    summary="Undo the last edit",
)
async def undo_edit(
    session_id: str,
    user: UserModel | None = Depends(get_current_user_or_none),
    service: ResumeEditService = Depends(get_resume_edit_service),
) -> ResumeEditUndoResponse:
    """Undo the most recent edit."""
    try:
        return await service.undo(session_id, user_id=user.id if user else None)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.post(
    "/resume-edit/session/{session_id}/redo",
    response_model=ResumeEditUndoResponse,
    summary="Redo the last undone edit",
)
async def redo_edit(
    session_id: str,
    user: UserModel | None = Depends(get_current_user_or_none),
    service: ResumeEditService = Depends(get_resume_edit_service),
) -> ResumeEditUndoResponse:
    """Redo the most recently undone edit."""
    try:
        return await service.redo(session_id, user_id=user.id if user else None)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
