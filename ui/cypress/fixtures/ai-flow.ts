/**
 * Shared mock fixtures for the AI screening pipeline.
 *
 * Every payload mirrors the backend response models exactly:
 *   - ResumeReviewResponse / FullReviewResult  → app/models/resume_review.py
 *   - ResumeEditCreateResponse / Apply / Undo  → app/models/resume_workspace.py
 *   - ResumeChatStartResponse / MessageResponse → app/models/resume_workspace.py
 *   - ApplyDecision / JobApplicationResult      → app/models/resume_workspace.py
 *   - LlmModelsResponse / JobDescription        → app/api/v1/llm.py, job_description.py
 */

export const RESUME_TEXT = `Alex Chen
Senior Software Engineer
Email: alex.chen@example.com | San Francisco, CA

SUMMARY
Results-driven Full-Stack Engineer with 5+ years of experience building web apps and APIs using Python, FastAPI, React, TypeScript, PostgreSQL, and Docker.

EXTRA EXPERIENCE
• Designed PostgreSQL database schemas and optimized complex SQL queries.

EXPERIENCE
Senior Backend Engineer | TechCorp Inc. (2022 - Present)
• Architected microservices using Python and FastAPI, improving API response speeds by 40%.
• Integrated Docker containerization into CI/CD pipelines.

SKILLS
Python, TypeScript, FastAPI, React, PostgreSQL, Docker, Git, Redis`;

export const EDITED_RESUME_TEXT = RESUME_TEXT.replace(
  "• Architected microservices using Python and FastAPI, improving API response speeds by 40%.",
  "• Architected Python/FastAPI microservices serving 2M+ req/day, cutting p95 latency by 40%.",
);

export const JOB_DESCRIPTION_TEXT = `We are searching for a Senior Full Stack Engineer.
Requirements:
• 4+ years software engineering experience.
• Strong proficiency in Python, FastAPI, React, TypeScript, PostgreSQL, and Docker.
• Experience with container deployment, cloud systems, and async services.`;

/** app/models/resume_review.py — FullReviewResult with all five agent payloads. */
export const FULL_REVIEW_RESULTS = {
  brutal_review: {
    overall_assessment:
      "Solid mid-senior profile but the bullets read like job duties, not achievements.",
    weak_areas: ["No quantified outcomes on 2 of 3 bullets", "Summary is generic"],
    missing_elements: ["No cloud certification", "No link to portfolio or GitHub"],
    immediate_rejections: [],
    strengths: ["Strong modern stack match", "Clear formatting"],
    actionable_fixes: [
      "Add measurable impact to each bullet",
      "Tailor the summary to the target JD",
    ],
  },
  ats_optimization: {
    ats_score_estimate: 62.5,
    missing_keywords: ["Kubernetes", "Kafka", "Terraform", "observability"],
    skills_to_highlight: ["Distributed systems", "CI/CD", "async services"],
    bullet_restructurings: [
      {
        original:
          "Architected microservices using Python and FastAPI, improving API response speeds by 40%.",
        suggested:
          "Architected Python/FastAPI microservices serving 2M+ req/day, cutting p95 latency by 40%.",
        reason: "Adds scale and latency metrics so ATS and recruiters see impact.",
      },
    ],
    summary: "JD match is strong on core stack; add infra keywords to pass automated screens.",
  },
  bullet_points: {
    original_bullets: [
      "Architected microservices using Python and FastAPI, improving API response speeds by 40%.",
    ],
    transformed_bullets: [
      {
        original:
          "Architected microservices using Python and FastAPI, improving API response speeds by 40%.",
        transformed:
          "Architected Python/FastAPI microservices that cut p95 API latency by 40%.",
        action_verb: "Architected",
        task: "Python/FastAPI microservices",
        result: "cut p95 API latency by 40%",
      },
    ],
    questions_for_user: ["What was peak traffic volume for these services?"],
  },
  industry_tone: {
    original_summary:
      "Results-driven Full-Stack Engineer with 5+ years of experience building web apps and APIs.",
    rewritten_summary:
      "Senior engineer shipping AI/SaaS products at scale: Python, FastAPI, React, and distributed PostgreSQL systems.",
    original_skills: ["Python", "React"],
    rewritten_skills: ["Python", "React", "Distributed PostgreSQL", "Event-driven APIs"],
    tone_analysis: "Summary now leads with scale and product impact for AI/SaaS audiences.",
    industry_alignment_score: 78.0,
  },
  final_polish: {
    tense_issues: [
      { section: "EXPERIENCE", original: "Designed PostgreSQL schemas", fixed: "Design PostgreSQL schemas" },
    ],
    cliche_replacements: [
      {
        original: "Results-driven",
        replacement: "Outcome-focused",
        reason: "Overused ATS cliche; a sharper opener stands out.",
      },
    ],
    generic_to_specific: [
      {
        original: "building web apps and APIs",
        improved: "building multi-tenant SaaS APIs on FastAPI",
      },
    ],
    overall_quality_score: 84.0,
    final_summary:
      "Resume is polished: quantified bullets, senior tone, and strong keyword coverage for the target role.",
  },
};

/** ResumeReviewResponse (app/models/resume_review.py service response). */
export const RESUME_REVIEW_RESPONSE = {
  results: FULL_REVIEW_RESULTS,
  resume_text: RESUME_TEXT,
  model_used: "meta-llama/llama-3.3-70b-instruct:free",
  processing_time_ms: 4210,
};

/** ResumeEditCreateResponse — app/models/resume_workspace.py */
export const EDIT_SESSION_RESPONSE = {
  session_id: "sess-e2e-001",
  content: RESUME_TEXT,
};

/** ResumeChatStartResponse */
export const CHAT_START_RESPONSE = {
  chat_id: "chat-e2e-001",
  history: [],
};

/** ResumeChatMessageResponse — assistant reply carrying one proposed edit. */
export const CHAT_MESSAGE_RESPONSE = {
  reply:
    "I rewrote your weakest bullet with scale metrics. Review the proposed edit below and apply it if it reads well.",
  proposed_edits: [
    {
      action_type: "replace",
      start_line: 14,
      end_line: 14,
      text: "• Architected Python/FastAPI microservices serving 2M+ req/day, cutting p95 latency by 40%.",
    },
  ],
  edits_summary: "Replaced 1 bullet with a quantified version.",
  needs_more_info: "",
  history: [
    { role: "user", content: "Rewrite my weakest bullet with metrics.", created_at: "2026-09-08T10:00:00Z" },
    {
      role: "assistant",
      content:
        "I rewrote your weakest bullet with scale metrics. Review the proposed edit below and apply it if it reads well.",
      created_at: "2026-09-08T10:00:05Z",
    },
  ],
};

/** ResumeEditApplyResponse after applying the proposed edit. */
export const EDIT_APPLY_RESPONSE = {
  document_id: "sess-e2e-001",
  content: EDITED_RESUME_TEXT,
  undo_available: true,
  redo_available: false,
  revision: 1,
};

/** ResumeEditUndoResponse — after undo the edit is redoable. */
export const EDIT_UNDO_RESPONSE = {
  document_id: "sess-e2e-001",
  content: RESUME_TEXT,
  undo_available: false,
  redo_available: true,
  revision: 2,
};

/** ApplyDecision — apply-agent verdict. */
export const READINESS_RESPONSE = {
  ready: true,
  application_status: "ready",
  summary: "Resume matches the JD requirements with quantified impact. Ready to submit.",
};

/** JobApplicationResult — application submission. */
export const APPLICATION_RESPONSE = {
  application_id: "app-e2e-001",
  status: "submitted",
  message: "Application submitted to TechCorp. Track it in your workspace.",
  submitted_at: "2026-09-08T10:05:00Z",
};

/** LlmModelsResponse — app/api/v1/llm.py */
export const LLM_MODELS_RESPONSE = {
  default_model: "meta-llama/llama-3.3-70b-instruct:free",
  models: [
    { id: "meta-llama/llama-3.3-70b-instruct:free", is_default: true },
    { id: "deepseek/deepseek-chat-v3:free", is_default: false },
  ],
};

/** JobDescription — app/models/job_description.py */
export const SAVED_JOBS = [
  {
    id: "jd-e2e-001",
    title: "Senior Full Stack Engineer",
    raw_text: JOB_DESCRIPTION_TEXT,
    min_work_experience: 4,
    max_work_experience: null,
    skills: ["Python", "FastAPI", "React", "TypeScript", "PostgreSQL", "Docker"],
  },
];

export const AUTH_USER = {
  id: "user-e2e-001",
  email: "candidate@example.com",
  name: "Alex Chen",
  avatar_url: null,
};
