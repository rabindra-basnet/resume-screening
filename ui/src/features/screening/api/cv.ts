import { apiUpload, apiPost, apiGet } from "@/shared/api/client";
import type {
  ResumeReviewResponse,
  ResumeEditCreateResponse,
  ResumeEditAction,
  ResumeEditApplyResponse,
  ResumeEditUndoResponse,
  ResumeChatStartResponse,
  ResumeChatMessageResponse,
  ResumeChatHistoryResponse,
  ApplyDecision,
} from "@/shared/types";

export function runResumeReview(params: {
  resume: File;
  reviewType: string;
  industry?: string;
  jobDescription?: string;
}): Promise<ResumeReviewResponse> {
  const form = new FormData();
  form.append("resume", params.resume);
  form.append("review_type", params.reviewType);
  if (params.industry) form.append("industry", params.industry);
  if (params.jobDescription) form.append("job_description", params.jobDescription);
  return apiUpload<ResumeReviewResponse>("/resume-review", form);
}

export function createEditSession(resume: File): Promise<ResumeEditCreateResponse> {
  const form = new FormData();
  form.append("resume", resume);
  return apiUpload<ResumeEditCreateResponse>("/resume-edit/session", form);
}

export function startChat(
  resumeText: string,
  resumeId?: string | null,
): Promise<ResumeChatStartResponse> {
  return apiPost<ResumeChatStartResponse>("/resume-chat", {
    resume_text: resumeText,
    resume_id: resumeId ?? null,
  });
}

export function sendChatMessage(
  chatId: string,
  content: string,
): Promise<ResumeChatMessageResponse> {
  return apiPost<ResumeChatMessageResponse>(
    `/resume-chat/${encodeURIComponent(chatId)}/message`,
    { content },
  );
}

export function applyChatEdit(
  chatId: string,
  documentId: string,
  action: ResumeEditAction,
): Promise<ResumeEditApplyResponse> {
  return apiPost<ResumeEditApplyResponse>(
    `/resume-chat/${encodeURIComponent(chatId)}/apply-edit`,
    { document_id: documentId, action },
  );
}

export function undoEdit(sessionId: string): Promise<ResumeEditUndoResponse> {
  return apiPost<ResumeEditUndoResponse>(
    `/resume-edit/session/${encodeURIComponent(sessionId)}/undo`,
    {},
  );
}

export function redoEdit(sessionId: string): Promise<ResumeEditUndoResponse> {
  return apiPost<ResumeEditUndoResponse>(
    `/resume-edit/session/${encodeURIComponent(sessionId)}/redo`,
    {},
  );
}

export function checkReadiness(
  chatId: string,
  editSessionId: string,
  jobDescription?: string,
): Promise<ApplyDecision> {
  const params = new URLSearchParams({ edit_session_id: editSessionId });
  if (jobDescription) params.set("job_description", jobDescription);
  return apiPost<ApplyDecision>(
    `/resume-chat/${encodeURIComponent(chatId)}/readiness?${params.toString()}`,
    {},
  );
}

export function getChatHistory(chatId: string): Promise<ResumeChatHistoryResponse> {
  return apiGet<ResumeChatHistoryResponse>(`/resume-chat/${encodeURIComponent(chatId)}`);
}
