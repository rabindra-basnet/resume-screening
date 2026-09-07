"""Resume chat + job application endpoints for the v1 API."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user_or_none, get_resume_chat_service
from app.database.schema import UserModel
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
    user: UserModel | None = Depends(get_current_user_or_none),
    payload: ResumeChatCreate = ResumeChatCreate(resume_text=""),
    service: ResumeChatService = Depends(get_resume_chat_service),
) -> dict:
    """Create a new chat session for iterative resume review."""
    context = ChatContext(
        resume_text=payload.resume_text,
    )
    return await service.start_chat(
        user_id=user.id if user else None,
        context=context,
        screening_id=payload.resume_id,
    )


@router.post("/resume-chat/{chat_id}/message", summary="Send a chat message")
async def send_chat_message(
    chat_id: str,
    payload: ResumeChatRequest,
    user: UserModel | None = Depends(get_current_user_or_none),
    service: ResumeChatService = Depends(get_resume_chat_service),
) -> dict:
    """Send a message and get the assistant reply with proposed edits."""
    try:
        return await service.send_message(
            chat_id=chat_id,
            user_id=user.id if user else None,
            content=payload.content,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/resume-chat/{chat_id}", summary="Get chat history")
async def get_chat_history(
    chat_id: str,
    user: UserModel | None = Depends(get_current_user_or_none),
    service: ResumeChatService = Depends(get_resume_chat_service),
) -> dict:
    """Return the message history of a chat session."""
    try:
        history = await service.get_history(chat_id=chat_id, user_id=user.id if user else None)
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
    user: UserModel | None = Depends(get_current_user_or_none),
    service: ResumeChatService = Depends(get_resume_chat_service),
) -> ResumeEditApplyResponse:
    """Apply a proposed edit to the linked editing session."""
    try:
        return await service.apply_edit(
            chat_id=chat_id,
            user_id=user.id if user else None,
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
    user: UserModel | None = Depends(get_current_user_or_none),
    service: ResumeChatService = Depends(get_resume_chat_service),
    edit_session_id: str | None = None,
    job_description: str = "",
) -> ApplyDecision:
    """Ask the readiness agent whether the edited resume is ready to apply."""
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
    user: UserModel | None = Depends(get_current_user_or_none),
    service: ResumeChatService = Depends(get_resume_chat_service),
) -> JobApplicationResult:
    """Persist a final job application after chat review."""
    if not payload.edit_session_id:
        raise HTTPException(status_code=422, detail="edit_session_id is required")
    try:
        return await service.submit_application(
            user_id=user.id if user else None,
            edit_session_id=payload.edit_session_id,
            payload=payload,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
