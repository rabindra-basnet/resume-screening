import { useState, useEffect } from "react";
import { useNavigate, useParams } from "@tanstack/react-router";
import type {
  ChatMessage,
  ChatProposedEdit,
  FullReviewResult,
} from "@/shared/types";
import { errMsg } from "@/shared/api/client";
import {
  runResumeReview,
  createEditSession,
  startChat,
  sendChatMessage,
  applyChatEdit,
  undoEdit,
  redoEdit,
} from "../api/cv";
import {
  useConversations,
  type Conversation,
} from "../hooks/useConversations";
import { ChatMessages } from "./ChatMessages";
import { ChatComposer } from "./ChatComposer";
import { ResumeDocument } from "./ResumeDocument";
import { type SetupState } from "./WorkspacePanel";
import { Button } from "@/shared/components/ui/button";
import { Bot, Sparkles, Wand2, ArrowLeft, PenTool, Target } from "lucide-react";

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
  const navigate = useNavigate();
  const params = useParams({ strict: false }) as { sessionId?: string };
  const routeSessionId = params.sessionId;

  const {
    conversations,
    active,
    setActiveId,
    createConversation,
    patchConversation,
    makeTitle,
  } = useConversations();

  // Sync active conversation when URL path param changes or initial load
  useEffect(() => {
    if (routeSessionId) {
      const match = conversations.find((c) => c.id === routeSessionId || c.chatId === routeSessionId);
      if (match && active?.id !== match.id) {
        setActiveId(match.id);
      }
    }
  }, [routeSessionId, conversations, active?.id, setActiveId]);

  // ── workspace state ───────────────────────────────────────────────────────
  const [setup, setSetup] = useState<SetupState>({
    selectedFile: null,
    pastedText: "",
    industry: "",
    jobDescription: "",
    model: "",
    jobMode: "paste",
  });

  const [busyReview, setBusyReview] = useState(false);
  const [busyChat, setBusyChat] = useState(false);
  const [statusText, setStatusText] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selection, setSelection] = useState<{ startLine: number; endLine: number; text: string } | null>(null);
  const [resumeText, setResumeText] = useState("");
  const [reviewResults, setReviewResults] = useState<FullReviewResult | null>(null);
  const [canUndo, setCanUndo] = useState(false);
  const [canRedo, setCanRedo] = useState(false);

  // Split-screen resizable layout state (Right pane width percentage relative to container width, default 45%)
  const [rightWidthPct, setRightWidthPct] = useState(45);
  const [isResizing, setIsResizing] = useState(false);

  const handleMouseDownSplitter = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
    const container = e.currentTarget.parentElement;
    if (!container) return;

    const rect = container.getBoundingClientRect();

    const onMouseMove = (moveEvent: MouseEvent) => {
      if (!rect.width) return;
      // Calculate right pane width percentage relative to container bounds
      const mouseOffsetFromRight = rect.right - moveEvent.clientX;
      const newRightWidthPct = (mouseOffsetFromRight / rect.width) * 100;
      // Clamp between 20% and 80%
      const clampedPct = Math.min(Math.max(newRightWidthPct, 20), 80);
      setRightWidthPct(clampedPct);
    };

    const onMouseUp = () => {
      setIsResizing(false);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
  };

  const chatId = active?.chatId ?? null;
  const editSessionId = active?.editSessionId ?? null;
  const messages = active?.messages ?? [];
  const hasSession = !!active && (!!chatId || !!editSessionId);

  const patchSetup = (patch: Partial<SetupState>) => setSetup((s) => ({ ...s, ...patch }));

  // ── pipeline run: creates a conversation + backend session binding ───────
  const runPipeline = async (opts?: { demo?: boolean; promptFocus?: string }) => {
    const promptFocus = opts?.promptFocus;
    const isDemoMode = !!opts?.demo || (!setup.selectedFile && !setup.pastedText.trim());
    const resumeText = isDemoMode ? (setup.pastedText.trim() || SAMPLE_RESUME_TEXT) : setup.pastedText;
    const jobDescription = setup.jobDescription.trim() ? setup.jobDescription : (isDemoMode ? SAMPLE_JOB_DESCRIPTION : "");
    const industry = setup.industry.trim() || "AI/SaaS";
    const file = isDemoMode ? null : setup.selectedFile;

    setError(null);
    setBusyReview(true);
    setStatusText("[1/5] BrutalReviewAgent — auditing experience & gaps…");

    // Ensure a conversation shell exists and becomes the binding target.
    const conv: Conversation = active && !active.chatId ? active : createConversation();
    if (!active || active.chatId) setActiveId(conv.id);

    // Redirect route URL to include the sessionId path parameter
    void navigate({ to: "/screen/$sessionId", params: { sessionId: conv.id } });

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
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setBusyReview(false);
      setStatusText(null);
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
    <div className="flex h-full min-h-0 flex-col overflow-hidden space-y-2">
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
        <div className="mx-auto flex h-full w-full max-w-3xl flex-col items-center justify-center overflow-hidden px-4 py-4" data-testid="workspace-root">
          {/* Glowing 3D Sphere Orb Header */}
          <div className="relative mb-4 flex items-center justify-center">
            <div className="h-14 w-14 rounded-full bg-gradient-to-tr from-cyan-400 via-blue-500 to-indigo-600 shadow-[0_0_35px_rgba(59,130,246,0.45)] transition-transform hover:scale-105" />
          </div>

          {/* Heading matching Screenshot 1 */}
          <h1 className="text-3xl font-bold tracking-tight text-[#1a1a1a] dark:text-white sm:text-4xl">
            What Can I help with?
          </h1>

          {/* Unified Central Chatbox Card matching Screenshot 1 */}
          <div className="mt-5 w-full" data-testid="quickstart-card">
            <ChatComposer
              busy={busyReview}
              selectedFile={setup.selectedFile}
              jobDescription={setup.jobDescription}
              showQuickPrompts={false}
              submitLabel={busyReview ? "Screening…" : "Voice"}
              onSend={(promptText) => {
                if (promptText) {
                  patchSetup({ pastedText: promptText });
                  void runPipeline({ promptFocus: promptText });
                } else {
                  void runPipeline();
                }
              }}
              onAttachFile={(f) => patchSetup({ selectedFile: f, pastedText: "" })}
              onRemoveFile={() => patchSetup({ selectedFile: null })}
              onJobDescriptionChange={(jd) => patchSetup({ jobDescription: jd })}
            />
          </div>

          {/* Suggestion Chips Row Below Card matching Screenshot 1 */}
          <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
            <button
              type="button"
              onClick={() => void runPipeline({ promptFocus: "Full 5-Agent Resume Optimization" })}
              className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3.5 py-1.5 text-xs font-medium text-slate-700 shadow-2xs transition-all hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:bg-card dark:text-slate-300"
            >
              <Sparkles size={13} className="text-blue-500" />
              <span>Optimize Resume</span>
            </button>
            <button
              type="button"
              onClick={() => void runPipeline({ promptFocus: "Analyze ATS Keyword Gaps & Match Score" })}
              className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3.5 py-1.5 text-xs font-medium text-slate-700 shadow-2xs transition-all hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:bg-card dark:text-slate-300"
            >
              <Target size={13} className="text-emerald-500" />
              <span>Analyze ATS Gaps</span>
            </button>
            <button
              type="button"
              onClick={() => void runPipeline({ promptFocus: "Transform Achievements to Action-Task-Result Bullets" })}
              className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3.5 py-1.5 text-xs font-medium text-slate-700 shadow-2xs transition-all hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:bg-card dark:text-slate-300"
            >
              <Wand2 size={13} className="text-purple-500" />
              <span>Bullet Transformer</span>
            </button>
            <button
              type="button"
              onClick={() => void runPipeline({ promptFocus: "Align Senior Industry Tone & Executive Summary" })}
              className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3.5 py-1.5 text-xs font-medium text-slate-700 shadow-2xs transition-all hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:bg-card dark:text-slate-300"
            >
              <PenTool size={13} className="text-orange-500" />
              <span>Senior Tone Match</span>
            </button>
          </div>

          <p className="mt-5 text-center text-[11px] text-slate-400">
            By messaging AI, you agree to our <span className="underline">Terms</span> and have read our <span className="underline">Privacy Policy</span>
          </p>

          <button
            type="button"
            className="mt-2 text-center text-xs font-medium text-slate-500 hover:text-blue-600"
            onClick={handleDemo}
            disabled={busyReview}
            data-testid="run-demo"
          >
            or try the 1-click live demo →
          </button>

          {busyReview && statusText && (
            <p className="mt-3 text-center text-xs font-medium text-blue-600 animate-pulse">{statusText}</p>
          )}
        </div>
      ) : (
        /* Page 2 — Split-Screen Workspace (2-Column Clean Layout: Left Chat | Right Document with Resizable Handle) */
        <div className="flex h-full min-h-0 flex-1 flex-col lg:flex-row gap-0 overflow-hidden relative select-none">
          {/* Chat column (Left) */}
          <div
            className="flex h-full min-h-0 flex-col rounded-2xl border border-border/60 bg-card/70 backdrop-blur transition-all duration-75"
            style={{ width: `calc(${100 - rightWidthPct}% - 6px)` }}
            data-testid="chat-column"
          >
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
              <div className="flex items-center gap-1.5">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 px-2 text-xs font-medium text-muted-foreground hover:text-foreground"
                  title="Reset split layout to 50/50"
                  onClick={() => setRightWidthPct(50)}
                >
                  50/50
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 px-2 text-xs font-medium text-muted-foreground hover:text-foreground"
                  title="Expand chat view"
                  onClick={() => setRightWidthPct(rightWidthPct === 20 ? 45 : 20)}
                >
                  {rightWidthPct === 20 ? "Shrink Chat" : "Expand Chat"}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="gap-1.5 rounded-xl font-medium"
                  onClick={() => {
                    createConversation();
                    void navigate({ to: "/screen" });
                  }}
                >
                  <ArrowLeft size={14} /> New Session
                </Button>
              </div>
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

          {/* Resizable Drag Splitter Divider */}
          <div
            onMouseDown={handleMouseDownSplitter}
            className={`hidden lg:flex w-3 hover:w-3 items-center justify-center cursor-col-resize group z-20 shrink-0 transition-colors ${
              isResizing ? "bg-primary/20" : "hover:bg-primary/10"
            }`}
            title="Drag to resize panels"
          >
            <div className={`w-1 h-8 rounded-full bg-border transition-colors group-hover:bg-primary ${
              isResizing ? "bg-primary" : ""
            }`} />
          </div>

          {/* Right Section: Document Preview ONLY */}
          <div
            className="flex h-full min-h-0 flex-col rounded-2xl border border-border/60 bg-card/70 p-4 backdrop-blur shadow-sm transition-all duration-75"
            style={{ width: `${rightWidthPct}%` }}
            data-testid="documents-column"
          >
            <ResumeDocument
              content={resumeText}
              canUndo={canUndo}
              canRedo={canRedo}
              busy={busyChat || busyReview}
              onContentChange={handleDocumentEdit}
              onUndo={handleUndo}
              onRedo={handleRedo}
              onSelectionChange={setSelection}
            />
          </div>
        </div>
      )}
    </div>
  );
}
