"""Resume chat + job application endpoints for the v1 API."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import CurrentUserDep, get_resume_chat_service
from app.models.resume_workspace import (
    ApplyDecision,
    ChatContext,
    JobApplicationPayload,
    JobApplicationResult,
    ResumeChatCreate,
    ResumeChatRequest,
    ResumeEditApplyRequest,
    ResumeEditApplyResponse,
)
from app.services import EditConflictError, ResumeChatService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["resume-chat"])


@router.post("/resume-chat", summary="Start a resume review chat session")
async def start_chat(
    ctx: CurrentUserDep,
    payload: ResumeChatCreate,
    service: ResumeChatService = Depends(get_resume_chat_service),
) -> dict:
    """Create a new chat session for iterative resume review.

    Args:
        ctx: Bundled session and authenticated user.
        payload: Resume text + optional resume context.
        service: The injected resume chat service.

    Returns:
        A dict with the chat id and the initial history.
    """
    context = ChatContext(
        resume_text=payload.resume_text,
    )
    return await service.start_chat(
        user_id=ctx.user_id,
        context=context,
        screening_id=payload.resume_id,
    )


@router.post("/resume-chat/{chat_id}/message", summary="Send a chat message")
async def send_chat_message(
    chat_id: str,
    payload: ResumeChatRequest,
    ctx: CurrentUserDep,
    service: ResumeChatService = Depends(get_resume_chat_service),
) -> dict:
    """Send a message and get the assistant reply with proposed edits.

    Args:
        chat_id: The chat session id.
        payload: The user's message.
        ctx: Bundled session and authenticated user.
        service: The injected resume chat service.

    Returns:
        A dict with the assistant reply, proposed edits, and history.

    Raises:
        HTTPException: 404 if the chat session is not found.
    """
    try:
        return await service.send_message(
            chat_id=chat_id,
            user_id=ctx.user_id,
            content=payload.content,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/resume-chat/{chat_id}", summary="Get chat history")
async def get_chat_history(
    chat_id: str,
    ctx: CurrentUserDep,
    service: ResumeChatService = Depends(get_resume_chat_service),
) -> dict:
    """Return the message history of a chat session.

    Args:
        chat_id: The chat session id.
        ctx: Bundled session and authenticated user.
        service: The injected resume chat service.

    Returns:
        A dict with the chat id and history.

    Raises:
        HTTPException: 404 if the chat session is not found.
    """
    try:
        history = await service.get_history(chat_id=chat_id, user_id=ctx.user_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"chat_id": chat_id, "history": history}


@router.post(
    "/resume-chat/{chat_id}/apply-edit",
    response_model=ResumeEditApplyResponse,
    summary="Apply a proposed chat edit",
)
async def apply_chat_edit(
    chat_id: str,
    payload: ResumeEditApplyRequest,
    ctx: CurrentUserDep,
    service: ResumeChatService = Depends(get_resume_chat_service),
) -> ResumeEditApplyResponse:
    """Apply a proposed edit to the linked editing session.

    Args:
        chat_id: The chat session id.
        payload: The edit (with the target editing session id).
        ctx: Bundled session and authenticated user.
        service: The injected resume chat service.

    Returns:
        The updated document state.

    Raises:
        HTTPException: 404 if the session is not found; 409 if the edit
            cannot be resolved against the current document state.
    """
    try:
        return await service.apply_edit(
            chat_id=chat_id,
            user_id=ctx.user_id,
            edit_session_id=payload.document_id,
            edit=payload.action,
        )
    except EditConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/resume-chat/{chat_id}/readiness", summary="Assess application readiness")
async def check_readiness(
    chat_id: str,
    ctx: CurrentUserDep,
    service: ResumeChatService = Depends(get_resume_chat_service),
    edit_session_id: str | None = None,
    job_description: str = "",
) -> ApplyDecision:
    """Ask the readiness agent whether the edited resume is ready to apply.

    Args:
        chat_id: The chat session id.
        ctx: Bundled session and authenticated user.
        edit_session_id: The editing session holding the final resume.
        job_description: Optional target job description.
        service: The injected resume chat service.

    Returns:
        An :class:`ApplyDecision`.

    Raises:
        HTTPException: 404 if the edit session is not found.
    """
    if not edit_session_id:
        raise HTTPException(status_code=422, detail="edit_session_id is required")
    try:
        return await service.decide_application(
            edit_session_id=edit_session_id,
            job_description=job_description,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/resume-chat/{chat_id}/apply",
    response_model=JobApplicationResult,
    summary="Submit a job application",
)
async def submit_application(
    chat_id: str,
    payload: JobApplicationPayload,
    ctx: CurrentUserDep,
    service: ResumeChatService = Depends(get_resume_chat_service),
) -> JobApplicationResult:
    """Persist a final job application after chat review.

    Args:
        chat_id: The chat session id.
        payload: Application details (final resume, cover letter, refs).
        ctx: Bundled session and authenticated user.
        service: The injected resume chat service.

    Returns:
        A :class:`JobApplicationResult`.

    Raises:
        HTTPException: 404 if the edit session is not found.
    """
    if not payload.edit_session_id:
        raise HTTPException(status_code=422, detail="edit_session_id is required")
    try:
        return await service.submit_application(
            user_id=ctx.user_id,
            edit_session_id=payload.edit_session_id,
            payload=payload,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
