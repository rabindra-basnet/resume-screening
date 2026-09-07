"""Resume editing endpoints supporting undo/redo."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.deps import CurrentUserDep, get_resume_edit_service
from app.config.constants import ALLOWED_EXTENSIONS, MAX_UPLOAD_BYTES
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
    ctx: CurrentUserDep,
    service: ResumeEditService = Depends(get_resume_edit_service),
    resume: UploadFile = File(...),
) -> dict:
    """Upload a resume and create an editable session seeded with its text.

    Args:
        ctx: Bundled session and authenticated user.
        resume: The resume file (PDF or DOCX).
        service: The injected resume editing service.

    Returns:
        A dict with the editing session id and the initial content.

    Raises:
        HTTPException: For validation errors or document parsing failures.
    """
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

    session_id = await service.create_session(
        resume_text=resume_text,
        user_id=ctx.user_id,
        resume_filename=filename,
    )
    return {"session_id": session_id, "content": resume_text}


@router.get("/resume-edit/session/{session_id}", summary="Get editing session content")
async def get_edit_session(
    session_id: str,
    ctx: CurrentUserDep,
    service: ResumeEditService = Depends(get_resume_edit_service),
) -> dict:
    """Return the current content of an editing session.

    Args:
        session_id: The editing session id.
        ctx: Bundled session and authenticated user.
        service: The injected resume editing service.

    Returns:
        A dict with the editing session id and content.
    """
    content = await service.get_content(session_id, user_id=ctx.user_id)
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
    ctx: CurrentUserDep,
    service: ResumeEditService = Depends(get_resume_edit_service),
) -> ResumeEditApplyResponse:
    """Apply a single line-based edit to the editing session.

    Args:
        session_id: The editing session id.
        payload: The edit action to apply.
        ctx: Bundled session and authenticated user.
        service: The injected resume editing service.

    Returns:
        The updated document state.

    Raises:
        HTTPException: 404 if the session is not found; 409 if the edit
            cannot be resolved against the current document state.
    """
    try:
        return await service.apply_edit(
            session_id, payload.action, user_id=ctx.user_id
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
    ctx: CurrentUserDep,
    service: ResumeEditService = Depends(get_resume_edit_service),
) -> ResumeEditUndoResponse:
    """Undo the most recent edit.

    Args:
        session_id: The editing session id.
        ctx: Bundled session and authenticated user.
        service: The injected resume editing service.

    Returns:
        The reverted document state.

    Raises:
        HTTPException: 404 if the session is not found or nothing to undo.
    """
    try:
        return await service.undo(session_id, user_id=ctx.user_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.post(
    "/resume-edit/session/{session_id}/redo",
    response_model=ResumeEditUndoResponse,
    summary="Redo the last undone edit",
)
async def redo_edit(
    session_id: str,
    ctx: CurrentUserDep,
    service: ResumeEditService = Depends(get_resume_edit_service),
) -> ResumeEditUndoResponse:
    """Redo the most recently undone edit.

    Args:
        session_id: The editing session id.
        ctx: Bundled session and authenticated user.
        service: The injected resume editing service.

    Returns:
        The re-applied document state.

    Raises:
        HTTPException: 404 if the session is not found or nothing to redo.
    """
    try:
        return await service.redo(session_id, user_id=ctx.user_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
