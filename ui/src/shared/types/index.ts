export interface HealthResponse {
  status: string;
  app: string;
  database: string;
}

export interface JobDescription {
  id: string | null;
  title: string | null;
  raw_text: string;
  min_work_experience: number | null;
  max_work_experience: number | null;
  skills: string[];
  created_at?: string | null;
}

export interface ScreeningCandidate {
  name: string | null;
  email: string | null;
  phone: string | null;
  education?: Array<{ degree?: string; field_of_study?: string; institution?: string }>;
  work_history?: Array<{ title?: string; company?: string; years?: number }>;
}

export interface ScreeningEvaluation {
  candidate_status: string;
  reason: string;
  matched_skills: string[];
  missing_skills: string[];
  weak_skills: string[];
  skill_match_percentage: number;
  experience_years: number | null;
}

export interface LearningResource {
  id?: string | null;
  skill: string;
  title: string;
  url: string;
  resource_type?: string;
  provider?: string;
  description?: string;
  estimated_hours?: number | null;
  screening_id?: string | null;
}

export interface LearningPlan {
  screening_id: string;
  candidate_name: string;
  skill_gaps: Array<{ skill: string; severity: string; reason: string }>;
  resources: LearningResource[];
  total_estimated_hours: number;
}

export interface ScreeningResult {
  candidate?: ScreeningCandidate;
  evaluation?: ScreeningEvaluation;
  learning_plan?: LearningPlan;
  model_used?: string;
}

// ── Resume Review (5 agents) ─────────────────────────────────────────────

export interface BrutalReviewResult {
  overall_assessment: string;
  weak_areas: string[];
  missing_elements: string[];
  immediate_rejections: string[];
  strengths: string[];
  actionable_fixes: string[];
}

export interface ATSBulletRestructuring {
  original: string;
  suggested: string;
  reason: string;
}

export interface ATSOptimizationResult {
  missing_keywords: string[];
  skills_to_highlight: string[];
  bullet_restructurings: ATSBulletRestructuring[];
  ats_score_estimate: number;
  summary: string;
}

export interface BulletTransform {
  original: string;
  transformed: string;
  action_verb: string;
  task: string;
  result: string;
}

export interface BulletPointResult {
  original_bullets: string[];
  transformed_bullets: BulletTransform[];
  questions_for_user: string[];
}

export interface IndustryToneResult {
  original_summary: string;
  rewritten_summary: string;
  original_skills: string[];
  rewritten_skills: string[];
  tone_analysis: string;
  industry_alignment_score: number;
}

export interface TenseIssue {
  section: string;
  original: string;
  fixed: string;
}

export interface ClicheReplacement {
  original: string;
  replacement: string;
  reason: string;
}

export interface GenericToSpecific {
  original: string;
  improved: string;
}

export interface FinalPolishResult {
  tense_issues: TenseIssue[];
  cliche_replacements: ClicheReplacement[];
  generic_to_specific: GenericToSpecific[];
  overall_quality_score: number;
  final_summary: string;
}

export interface FullReviewResult {
  brutal_review?: BrutalReviewResult | null;
  ats_optimization?: ATSOptimizationResult | null;
  bullet_points?: BulletPointResult | null;
  industry_tone?: IndustryToneResult | null;
  final_polish?: FinalPolishResult | null;
}

export interface ResumeReviewResponse {
  review_id: string;
  review_type: string;
  results: FullReviewResult;
  resume_text: string;
  model_used: string;
  processing_time_ms: number;
}

// ── Chat / Iterative Review ──────────────────────────────────────────────

export interface ChatMessage {
  id?: string | null;
  role: "user" | "assistant" | "system";
  content: string;
  created_at?: string | null;
  /** Assistant messages may carry proposed edits (not persisted server-side as
   * part of the history payload, but attached client-side for rendering). */
  proposed_edits?: ChatProposedEdit[];
}

export interface ResumeChatCreateRequest {
  resume_text: string;
  resume_id?: string | null;
}

export interface ResumeChatRequest {
  content: string;
}

export interface ChatProposedEdit {
  action_type: "insert" | "replace" | "delete" | string;
  start_line: number;
  end_line: number;
  text: string;
}

export interface ChatReply {
  reply: string;
  proposed_edits: ChatProposedEdit[];
  edits_summary: string;
  needs_more_info: string;
}

export interface ResumeChatStartResponse {
  chat_id: string;
  history: ChatMessage[];
}

export interface ResumeChatMessageResponse {
  reply: string;
  proposed_edits: ChatProposedEdit[];
  edits_summary: string;
  needs_more_info: string;
  history: ChatMessage[];
}

export interface ResumeChatHistoryResponse {
  chat_id: string;
  history: ChatMessage[];
}

// ── Editing (undo/redo) ──────────────────────────────────────────────────

export interface ResumeEditAction {
  action_type: "insert" | "replace" | "delete";
  /**
   * 0-based line index where the edit starts. When `previous_text` is
   * provided it is treated as a hint only — the server resolves the true
   * location by matching `previous_text` against its current content to
   * avoid drift from other edits.
   */
  start_line: number;
  /** 0-based end line (exclusive for replace). Also a hint when anchoring. */
  end_line: number;
  text: string;
  /**
   * Authoritative anchor for `replace`/`delete`: the exact line(s) the client
   * expects at this location. The server matches these against its current
   * content; if not found it returns a 409 conflict so the client re-syncs.
   * For `insert`, it is the line after which to insert.
   */
  previous_text?: string;
  /** Server-set timestamp (UTC ISO-8601); not required from the client. */
  timestamp?: string;
}

export interface ResumeEditApplyRequest {
  document_id: string;
  action: ResumeEditAction;
}

export interface ResumeEditApplyResponse {
  document_id: string;
  content: string;
  undo_available: boolean;
  redo_available: boolean;
  revision: number;
}

export interface ResumeEditCreateResponse {
  session_id: string;
  content: string;
}

export interface ResumeEditUndoResponse {
  document_id: string;
  content: string;
  undo_available: boolean;
  redo_available: boolean;
  revision: number;
}

// ── Job Application ──────────────────────────────────────────────────────

export interface JobApplicationPayload {
  edit_session_id?: string | null;
  screening_id?: string | null;
  job_id?: string | null;
  resume_text: string;
  cover_letter: string;
  notes: string;
}

export interface JobApplicationResult {
  application_id: string;
  status: "submitted" | "queued" | "failed";
  message: string;
  submitted_at: string;
}

export interface ApplyDecision {
  ready: boolean;
  application_status: "ready" | "needs_review" | "not_ready";
  summary: string;
}
