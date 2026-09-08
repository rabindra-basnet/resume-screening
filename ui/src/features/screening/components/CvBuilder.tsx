import { useEffect, useState } from "react";
import type {
  ChatMessage,
  ChatProposedEdit,
  FullReviewResult,
  JobDescription,
  LlmModelInfo,
  ApplyDecision,
  JobApplicationResult,
} from "@/shared/types";
import { api, errMsg } from "@/shared/api/client";
import {
  runResumeReview,
  createEditSession,
  startChat,
  sendChatMessage,
  applyChatEdit,
  undoEdit,
  redoEdit,
  checkReadiness,
  listLlmModels,
  listJobDescriptions,
} from "../api/cv";
import {
  useConversations,
  type Conversation,
} from "../hooks/useConversations";
import { ConversationsSidebar } from "./ConversationsSidebar";
import { ChatMessages } from "./ChatMessages";
import { ChatComposer } from "./ChatComposer";
import { WorkspacePanel, type SetupState } from "./WorkspacePanel";
import { Button } from "@/shared/components/ui/button";
import { Textarea } from "@/shared/components/ui/textarea";
import { Bot, Sparkles, Wand2, RefreshCw, ArrowLeft, Paperclip, Globe, Lightbulb, PenTool, Target } from "lucide-react";

const SAMPLE_RESUME_TEXT = `Alex Chen
Senior Software Engineer
Email: alex.chen@example.com | San Francisco, CA

SUMMARY
Results-driven Full-Stack Engineer with 5+ years of experience building web apps and APIs using Python, FastAPI, React, TypeScript, PostgreSQL, and Docker.

EXPERIENCE
Senior Backend Engineer | TechCorp Inc. (2022 - Present)
• Architected microservices using Python and FastAPI, improving API response speeds by 40%.
• Designed PostgreSQL database schemas and optimized complex SQL queries.
• Integrated Docker containerization into CI/CD pipelines.

SKILLS
Python, TypeScript, FastAPI, React, PostgreSQL, Docker, Git, Redis`;

const SAMPLE_JOB_DESCRIPTION = `We are searching for a Senior Full Stack Engineer.
Requirements:
• 4+ years software engineering experience.
• Strong proficiency in Python, FastAPI, React, TypeScript, PostgreSQL, and Docker.
• Experience with container deployment, cloud systems, and async services.`;

export function CvBuilder() {
  const {
    conversations,
    activeId,
    active,
    setActiveId,
    createConversation,
    patchConversation,
    deleteConversation,
    makeTitle,
  } = useConversations();

  // ── workspace state ───────────────────────────────────────────────────────
  const [panelTab, setPanelTab] = useState<"setup" | "report" | "resume">("setup");
  const [setup, setSetup] = useState<SetupState>({
    selectedFile: null,
    pastedText: "",
    industry: "",
    jobDescription: "",
    model: "",
    jobMode: "paste",
  });
  const [savedJobs, setSavedJobs] = useState<JobDescription[]>([]);
  const [models, setModels] = useState<LlmModelInfo[]>([]);

  // ── run state ─────────────────────────────────────────────────────────────
  const [busyReview, setBusyReview] = useState(false);
  const [busyChat, setBusyChat] = useState(false);
  const [statusText, setStatusText] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // ── document + results ───────────────────────────────────────────────────
  const [resumeText, setResumeText] = useState("");
  const [reviewResults, setReviewResults] = useState<FullReviewResult | null>(null);
  const [canUndo, setCanUndo] = useState(false);
  const [canRedo, setCanRedo] = useState(false);
  const [readiness, setReadiness] = useState<ApplyDecision | null>(null);
  const [applyResult, setApplyResult] = useState<string | null>(null);
  const [selection, setSelection] = useState<{
    text: string;
    startLine: number;
    endLine: number;
  } | null>(null);

  const chatId = active?.chatId ?? null;
  const editSessionId = active?.editSessionId ?? null;
  const messages = active?.messages ?? [];
  const hasSession = !!active && (!!chatId || !!editSessionId);

  // Load saved JDs and model list once on mount.
  useEffect(() => {
    (async () => {
      try {
        const [jobs, modelResp] = await Promise.all([listJobDescriptions(), listLlmModels()]);
        setSavedJobs(jobs || []);
        setModels(modelResp.models || []);
        setSetup((s) => ({ ...s, model: s.model || modelResp.default_model || modelResp.models?.[0]?.id || "" }));
      } catch {
        // Non-fatal; default model is used server-side.
      }
    })();
  }, []);

  const patchSetup = (patch: Partial<SetupState>) => setSetup((s) => ({ ...s, ...patch }));

  const setPanelForState = () => {
    if (reviewResults) setPanelTab("report");
  };

  // ── pipeline run: creates a conversation + backend session binding ───────
  const runPipeline = async (opts?: { demo?: boolean; promptFocus?: string }) => {
    const promptFocus = opts?.promptFocus;
    const isDemoMode = !!opts?.demo || (!setup.selectedFile && !setup.pastedText.trim());
    const resumeText = isDemoMode ? (setup.pastedText.trim() || SAMPLE_RESUME_TEXT) : setup.pastedText;
    const jobDescription = setup.jobDescription.trim() ? setup.jobDescription : (isDemoMode ? SAMPLE_JOB_DESCRIPTION : "");
    const industry = setup.industry.trim() || "AI/SaaS";
    const file = isDemoMode ? null : setup.selectedFile;

    setError(null);
    setApplyResult(null);
    setReadiness(null);
    setBusyReview(true);
    setStatusText("[1/5] BrutalReviewAgent — auditing experience & gaps…");

    // Ensure a conversation shell exists and becomes the binding target.
    const conv: Conversation = active && !active.chatId ? active : createConversation();
    if (!active || active.chatId) setActiveId(conv.id);

    // Reset per-run results.
    setReviewResults(null);
    setCanUndo(false);
    setCanRedo(false);

    try {
      setStatusText("[2/5] ATSOptimizerAgent — scoring keywords & job description fit…");
      const data = await runResumeReview({
        resume: file,
        resumeText: file ? "" : resumeText,
        reviewType: "full",
        industry,
        jobDescription,
        model: setup.model || undefined,
      });

      setStatusText("[3/5] BulletTransformerAgent — converting achievements to Action-Task-Result…");
      const parsed = data.resume_text || resumeText;
      setResumeText(parsed);
      setReviewResults(data.results as FullReviewResult);

      const userBubbleText = promptFocus
        ? `${promptFocus}${jobDescription ? " (Target JD attached)" : ""}`
        : (isDemoMode && !setup.selectedFile && !setup.pastedText.trim()
            ? "Run 1-click demo screening."
            : `Screen & optimize resume${jobDescription ? " against target JD" : ""}.`);

      const userBubble: ChatMessage = {
        role: "user",
        content: userBubbleText,
        id: null,
        created_at: new Date().toISOString(),
      };
      patchConversation(conv.id, { title: makeTitle(parsed), messages: [userBubble] });

      setStatusText("[4/5] IndustryToneMatchAgent — binding live editable session…");
      const edit = file ? await createEditSession(file) : await createEditSession(null, parsed);

      setStatusText("[5/5] FinalPolishAgent — initializing conversational assistant…");
      const chat = await startChat(parsed, null, {
        jobDescription,
        industry,
        model: setup.model || undefined,
      });

      const greeting: ChatMessage = {
        role: "assistant",
        content: promptFocus
          ? `Optimization focused on: "${promptFocus}". The five-agent report is ready in the Report tab — ask me to apply any fix or edit specific resume lines on the right.`
          : "Screening complete. The five-agent report is in the Report tab — ask me to apply any fix, rewrite a section, or highlight a part of the resume on the right and I'll target exactly those lines.",
        id: null,
        created_at: new Date().toISOString(),
      };
      patchConversation(conv.id, {
        chatId: chat.chat_id,
        editSessionId: edit.session_id,
        messages: [userBubble, greeting],
      });

      setPanelTab("report");
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setBusyReview(false);
      setStatusText(null);
      setPanelForState();
    }
  };

  // ── chat send ─────────────────────────────────────────────────────────────
  const handleSend = async (content: string) => {
    if (!active) {
      createConversation();
      return;
    }
    const convId = active.id;

    const userMsg: ChatMessage = {
      role: "user",
      content,
      id: null,
      created_at: new Date().toISOString(),
      // Client-side metadata: shown as a targeting chip on the user bubble.
    } as ChatMessage & { selection?: typeof selection };
    (userMsg as { selection?: typeof selection }).selection = selection;

    const prevMessages = active.messages;
    patchConversation(convId, { messages: [...prevMessages, userMsg] });

    // Optimistic placeholder assistant message is avoided; a busy indicator renders instead.
    setBusyChat(true);
    setError(null);
    try {
      const data = await sendChatMessage(chatId!, content, { model: setup.model || undefined });
      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: data.reply,
        id: null,
        created_at: new Date().toISOString(),
        proposed_edits: (data.proposed_edits || []) as ChatProposedEdit[],
      };
      patchConversation(convId, { messages: [...prevMessages, userMsg, assistantMsg] });
      // Clear selection after a targeted request has been dispatched.
      setSelection(null);
    } catch (err) {
      setError(errMsg(err));
      patchConversation(convId, { messages: prevMessages });
    } finally {
      setBusyChat(false);
    }
  };

  // ── edit application (proposed edits + manual document edits) ────────────
  const handleApplyProposed = async (edit: ChatProposedEdit) => {
    if (!chatId || !editSessionId || !active) return;
    setBusyChat(true);
    setError(null);
    try {
      const res = await applyChatEdit(chatId, editSessionId, {
        action_type: edit.action_type as "insert" | "replace" | "delete",
        start_line: edit.start_line,
        end_line: edit.end_line,
        text: edit.text,
        previous_text: "",
      });
      setCanUndo(res.undo_available);
      setCanRedo(res.redo_available);
      setResumeText(res.content);
      setPanelTab("resume");
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setBusyChat(false);
    }
  };

  const handleDocumentEdit = async (text: string) => {
    if (!chatId || !editSessionId) {
      // No backend session bound yet — keep the local edit only.
      setResumeText(text);
      return;
    }
    setBusyChat(true);
    setError(null);
    try {
      // Persist manual edits as a replace of the full document so undo covers it.
      const lineCount = resumeText ? resumeText.split("\n").length : 0;
      const res = await applyChatEdit(chatId, editSessionId, {
        action_type: "replace",
        start_line: 1,
        end_line: Math.max(lineCount, text.split("\n").length),
        text,
        previous_text: resumeText,
      });
      setCanUndo(res.undo_available);
      setCanRedo(res.redo_available);
      setResumeText(res.content);
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setBusyChat(false);
    }
  };

  const handleUndo = async () => {
    if (!editSessionId) return;
    setError(null);
    try {
      const res = await undoEdit(editSessionId);
      setCanUndo(res.undo_available);
      setCanRedo(res.redo_available);
      setResumeText(res.content);
    } catch (err) {
      setError(errMsg(err));
    }
  };

  const handleRedo = async () => {
    if (!editSessionId) return;
    setError(null);
    try {
      const res = await redoEdit(editSessionId);
      setCanUndo(res.undo_available);
      setCanRedo(res.redo_available);
      setResumeText(res.content);
    } catch (err) {
      setError(errMsg(err));
    }
  };

  // ── readiness + apply ─────────────────────────────────────────────────────
  const handleReadiness = async () => {
    if (!chatId || !editSessionId) return;
    setError(null);
    try {
      const res = await checkReadiness(
        chatId,
        editSessionId,
        setup.jobDescription || undefined,
        setup.model || undefined,
      );
      setReadiness(res);
    } catch (err) {
      setError(errMsg(err));
    }
  };

  const handleApply = async () => {
    if (!chatId || !editSessionId) return;
    setError(null);
    try {
      const res = await api
        .post(`/resume-chat/${encodeURIComponent(chatId)}/apply`, {
          edit_session_id: editSessionId,
          resume_text: resumeText,
          cover_letter: "",
          notes: "",
        })
        .then((r) => r.data as JobApplicationResult);
      setApplyResult(res.message || `Application submitted (${res.status || "ok"})`);
    } catch (err) {
      setError(errMsg(err));
    }
  };

  const handleDemo = () => {
    setSetup((s) => ({
      ...s,
      pastedText: SAMPLE_RESUME_TEXT,
      jobDescription: SAMPLE_JOB_DESCRIPTION,
      industry: "AI/SaaS",
      selectedFile: null,
    }));
    void runPipeline({ demo: true });
  };

  // ── render ────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-4">
      {error && (
        <div className="flex items-start gap-2 rounded-xl border border-destructive/30 bg-destructive/5 px-3.5 py-2.5 text-sm text-destructive" data-testid="workspace-error">
          <span className="flex-1">{error}</span>
          <button className="text-xs underline" onClick={() => setError(null)}>
            dismiss
          </button>
        </div>
      )}

      {/* ROOT: Page 1 — Hero Landing State (Matching Screenshot 1 pixel-for-pixel) */}
      {!hasSession ? (
        <div className="mx-auto flex min-h-[82vh] w-full max-w-3xl flex-col items-center justify-center px-4 py-6" data-testid="workspace-root">
          {/* Glowing 3D Sphere Orb Header */}
          <div className="relative mb-5 flex items-center justify-center">
            <div className="h-16 w-16 rounded-full bg-gradient-to-tr from-cyan-400 via-blue-500 to-indigo-600 shadow-[0_0_35px_rgba(59,130,246,0.45)] transition-transform hover:scale-105" />
          </div>

          {/* Heading matching Screenshot 1 */}
          <h1 className="text-3xl font-bold tracking-tight text-[#1a1a1a] dark:text-white sm:text-4xl">
            What Can I help with?
          </h1>

          {/* Main Central Input Box Card matching Screenshot 1 */}
          <div className="mt-7 w-full rounded-2xl border border-slate-200/90 bg-white p-4 shadow-[0_4px_24px_rgba(0,0,0,0.04)] dark:border-slate-800 dark:bg-card" data-testid="quickstart-card">
            <div className="space-y-3">
              <div className="flex items-center justify-between px-1">
                <span className="text-xs font-semibold text-slate-400">Ask anything</span>
                <label className="inline-flex cursor-pointer items-center gap-1 text-xs font-medium text-blue-600 hover:underline">
                  <span>Upload PDF/DOCX</span>
                  <input
                    type="file"
                    accept=".pdf,.docx"
                    className="hidden"
                    data-testid="qs-file-input"
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) patchSetup({ selectedFile: f, pastedText: "" });
                    }}
                  />
                </label>
              </div>

              {setup.selectedFile ? (
                <div className="flex items-center justify-between rounded-xl border border-emerald-500/40 bg-emerald-50 px-3.5 py-2 text-sm font-medium text-emerald-700">
                  <span className="truncate">{setup.selectedFile.name}</span>
                  <button
                    type="button"
                    className="text-xs font-semibold text-slate-400 hover:text-red-500"
                    onClick={() => patchSetup({ selectedFile: null })}
                  >
                    remove
                  </button>
                </div>
              ) : (
                <Textarea
                  id="qs-resume"
                  value={setup.pastedText}
                  onChange={(e) => patchSetup({ pastedText: e.target.value, selectedFile: null })}
                  placeholder="Ask anything or paste job description / resume text…"
                  rows={3}
                  className="w-full resize-none border-none bg-transparent px-1 py-1 text-sm text-slate-800 placeholder:text-slate-400 focus-visible:ring-0 dark:text-slate-100"
                  data-testid="qs-resume-input"
                />
              )}

              <div className="rounded-xl bg-slate-50/80 p-2.5 dark:bg-slate-900/50">
                <Textarea
                  id="qs-jd"
                  value={setup.jobDescription}
                  onChange={(e) => patchSetup({ jobDescription: e.target.value })}
                  placeholder="Target Job Description (optional — improves ATS match scoring)…"
                  rows={2}
                  className="w-full resize-none border-none bg-transparent px-1 text-xs text-slate-700 placeholder:text-slate-400 focus-visible:ring-0 dark:text-slate-300"
                  data-testid="qs-jd-input"
                />
              </div>
            </div>

            {/* In-Card Action Bar matching Screenshot 1 */}
            <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 pt-3 dark:border-slate-800">
              <div className="flex flex-wrap items-center gap-2">
                <label className="inline-flex cursor-pointer items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3.5 py-1.5 text-xs font-medium text-slate-700 shadow-2xs transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200">
                  <Paperclip size={13} className="text-slate-500" />
                  <span>Attach</span>
                  <input
                    type="file"
                    accept=".pdf,.docx"
                    className="hidden"
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) patchSetup({ selectedFile: f, pastedText: "" });
                    }}
                  />
                </label>

                <button
                  type="button"
                  onClick={() => patchSetup({ jobMode: setup.jobMode === "saved" ? "paste" : "saved" })}
                  className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3.5 py-1.5 text-xs font-medium text-slate-700 shadow-2xs transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                >
                  <Globe size={13} className="text-slate-500" />
                  <span>Search</span>
                </button>

                <button
                  type="button"
                  className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3.5 py-1.5 text-xs font-medium text-slate-700 shadow-2xs transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                >
                  <Lightbulb size={13} className="text-amber-500" />
                  <span>Reason</span>
                </button>
              </div>

              <Button
                onClick={() => void runPipeline()}
                disabled={busyReview || (!setup.selectedFile && !setup.pastedText.trim())}
                className="inline-flex items-center gap-1.5 rounded-full bg-[#ff5c00] px-5 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-[#e55300]"
                data-testid="run-screening"
              >
                {busyReview ? (
                  <>
                    <RefreshCw className="animate-spin" size={13} /> Screening…
                  </>
                ) : (
                  <>
                    <Bot size={13} /> Voice
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Suggestion Chips Row Below Card matching Screenshot 1 */}
          <div className="mt-5 flex flex-wrap items-center justify-center gap-2.5">
            <button
              type="button"
              onClick={() => void runPipeline({ promptFocus: "Full 5-Agent Resume Optimization" })}
              className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-4 py-1.5 text-xs font-medium text-slate-700 shadow-2xs transition-all hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:bg-card dark:text-slate-300"
            >
              <Sparkles size={13} className="text-blue-500" />
              <span>Optimize Resume</span>
            </button>
            <button
              type="button"
              onClick={() => void runPipeline({ promptFocus: "Analyze ATS Keyword Gaps & Match Score" })}
              className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-4 py-1.5 text-xs font-medium text-slate-700 shadow-2xs transition-all hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:bg-card dark:text-slate-300"
            >
              <Target size={13} className="text-emerald-500" />
              <span>Analyze ATS Gaps</span>
            </button>
            <button
              type="button"
              onClick={() => void runPipeline({ promptFocus: "Transform Achievements to Action-Task-Result Bullets" })}
              className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-4 py-1.5 text-xs font-medium text-slate-700 shadow-2xs transition-all hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:bg-card dark:text-slate-300"
            >
              <Wand2 size={13} className="text-purple-500" />
              <span>Bullet Transformer</span>
            </button>
            <button
              type="button"
              onClick={() => void runPipeline({ promptFocus: "Align Senior Industry Tone & Executive Summary" })}
              className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-4 py-1.5 text-xs font-medium text-slate-700 shadow-2xs transition-all hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:bg-card dark:text-slate-300"
            >
              <PenTool size={13} className="text-orange-500" />
              <span>Senior Tone Match</span>
            </button>
          </div>

          <p className="mt-8 text-center text-[11px] text-slate-400">
            By messaging AI, you agree to our <span className="underline">Terms</span> and have read our <span className="underline">Privacy Policy</span>
          </p>

          <button
            type="button"
            className="mt-3 text-center text-xs font-medium text-slate-500 hover:text-blue-600"
            onClick={handleDemo}
            disabled={busyReview}
            data-testid="run-demo"
          >
            or try the 1-click live demo →
          </button>

          {busyReview && statusText && (
            <p className="mt-4 text-center text-xs font-medium text-blue-600 animate-pulse">{statusText}</p>
          )}
        </div>
      ) : (
        /* Page 2 — Split-Screen Workspace (Matching Screenshot 2 Lovable style) */
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[230px_minmax(0,1fr)_400px]">
          <div className="hidden min-h-0 xl:block">
            <ConversationsSidebar
              conversations={conversations}
              activeId={activeId}
              onSelect={setActiveId}
              onNew={() => {
                createConversation();
                setPanelTab("setup");
              }}
              onDelete={deleteConversation}
            />
          </div>

          {/* Chat column */}
          <div className="flex min-h-[72vh] flex-col rounded-2xl border border-border/60 bg-card/70 backdrop-blur" data-testid="chat-column">
            <div className="flex items-center justify-between gap-2 border-b border-border/40 px-4 py-3">
              <div className="flex min-w-0 items-center gap-2.5">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <Bot size={17} />
                </div>
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold leading-tight">
                    {active?.title || "Screening assistant"}
                  </p>
                  <p className="text-[11px] text-muted-foreground">
                    {busyReview
                      ? "Orchestrating 5 agents…"
                      : reviewResults
                      ? "Report ready — iterate via chat"
                      : "Assistant ready"}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="gap-1.5 xl:hidden"
                onClick={() => {
                  createConversation();
                  setPanelTab("setup");
                }}
              >
                <ArrowLeft size={14} /> New
              </Button>
            </div>

            <div className="flex min-h-0 flex-1 flex-col px-4">
              <ChatMessages
                messages={messages}
                reviewResults={reviewResults}
                busy={busyChat || busyReview}
                statusText={statusText}
                selection={selection}
                onApplyProposed={handleApplyProposed}
                hasResume={!!resumeText}
              />
              <div className="shrink-0 border-t border-border/40 py-3">
                <ChatComposer
                  busy={busyChat || busyReview}
                  canUndo={canUndo}
                  canRedo={canRedo}
                  hasSelection={!!selection}
                  onSend={handleSend}
                  onUndo={handleUndo}
                  onRedo={handleRedo}
                />
              </div>
            </div>
          </div>

          {/* Documents column */}
          <div className="min-h-[72vh] rounded-2xl border border-border/60 bg-card/70 p-3 backdrop-blur" data-testid="documents-column">
            <WorkspacePanel
              tab={panelTab}
              onTabChange={setPanelTab}
              setup={setup}
              onSetupChange={patchSetup}
              savedJobs={savedJobs}
              models={models}
              resumeContent={resumeText}
              canUndo={canUndo}
              canRedo={canRedo}
              busyReview={busyReview}
              busy={busyChat}
              reviewResults={reviewResults}
              readiness={readiness}
              applyResult={applyResult}
              onRunScreening={() => void runPipeline()}
              onResumeContentChange={handleDocumentEdit}
              onUndo={handleUndo}
              onRedo={handleRedo}
              onReadiness={handleReadiness}
              onApply={handleApply}
              onSelectionChange={setSelection}
            />
          </div>
        </div>
      )}
    </div>
  );
}
