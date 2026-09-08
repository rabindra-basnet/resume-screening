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
  LlmModelsResponse,
  JobDescription,
} from "@/shared/types";

export function runResumeReview(params: {
  resume?: File | null;
  resumeText?: string;
  reviewType: string;
  industry?: string;
  jobDescription?: string;
  model?: string;
}): Promise<ResumeReviewResponse> {
  const form = new FormData();
  if (params.resume) form.append("resume", params.resume);
  if (params.resumeText) form.append("resume_text", params.resumeText);
  form.append("review_type", params.reviewType);
  if (params.industry) form.append("industry", params.industry);
  if (params.jobDescription) form.append("job_description", params.jobDescription);
  if (params.model) form.append("model_override", params.model);
  return apiUpload<ResumeReviewResponse>("/resume-review", form);
}

export function createEditSession(
  resume?: File | null,
  resumeText?: string,
): Promise<ResumeEditCreateResponse> {
  const form = new FormData();
  if (resume) form.append("resume", resume);
  if (resumeText) form.append("resume_text", resumeText);
  return apiUpload<ResumeEditCreateResponse>("/resume-edit/session", form);
}

export function startChat(
  resumeText: string,
  resumeId?: string | null,
  opts?: { jobDescription?: string; industry?: string; model?: string },
): Promise<ResumeChatStartResponse> {
  return apiPost<ResumeChatStartResponse>("/resume-chat", {
    resume_text: resumeText,
    resume_id: resumeId ?? null,
    job_description: opts?.jobDescription ?? "",
    industry: opts?.industry ?? "",
    model_override: opts?.model ?? null,
  });
}

export function sendChatMessage(
  chatId: string,
  content: string,
  opts?: { model?: string },
): Promise<ResumeChatMessageResponse> {
  return apiPost<ResumeChatMessageResponse>(
    `/resume-chat/${encodeURIComponent(chatId)}/message`,
    { content, model_override: opts?.model ?? null },
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
  model?: string,
): Promise<ApplyDecision> {
  const params = new URLSearchParams({ edit_session_id: editSessionId });
  if (jobDescription) params.set("job_description", jobDescription);
  if (model) params.set("model_override", model);
  return apiPost<ApplyDecision>(
    `/resume-chat/${encodeURIComponent(chatId)}/readiness?${params.toString()}`,
    {},
  );
}

export function getChatHistory(chatId: string): Promise<ResumeChatHistoryResponse> {
  return apiGet<ResumeChatHistoryResponse>(`/resume-chat/${encodeURIComponent(chatId)}`);
}

export function listLlmModels(): Promise<LlmModelsResponse> {
  return apiGet<LlmModelsResponse>("/llm/models");
}

export function listJobDescriptions(): Promise<JobDescription[]> {
  return apiGet<JobDescription[]>("/job-descriptions");
}
