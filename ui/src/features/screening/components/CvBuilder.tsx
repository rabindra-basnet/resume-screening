import { useState } from "react";
import type {
  FullReviewResult,
  ChatMessage,
  ChatProposedEdit,
  ResumeEditAction,
  ApplyDecision,
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
} from "../api/cv";
import type { JobApplicationResult } from "@/shared/types";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Label } from "@/shared/components/ui/label";
import { Textarea } from "@/shared/components/ui/textarea";
import { Input } from "@/shared/components/ui/input";
import { Badge } from "@/shared/components/ui/badge";
import { Separator } from "@/shared/components/ui/separator";
import { ResumeDropzone } from "./ResumeDropzone";
import { CvReviewResults } from "./CvReviewResults";
import { CvChatPanel } from "./CvChatPanel";
import {
  Sparkles,
  RefreshCw,
  AlertCircle,
  FileText,
  MessageSquare,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Rocket,
  ShieldCheck,
  Target,
  PenLine,
  Music2,
  MicVocal,
  Check,
  Gauge,
} from "lucide-react";

const REVIEW_TYPES: { value: string; label: string; hint: string; icon: typeof Sparkles; accent: string }[] = [
  {
    value: "full",
    label: "Full Review",
    hint: "Run all 5 agents",
    icon: Gauge,
    accent: "from-primary/20 to-primary/5 text-primary",
  },
  {
    value: "brutal",
    label: "Brutal Honest",
    hint: "Hiring-manager critique",
    icon: ShieldCheck,
    accent: "from-rose-500/20 to-rose-500/5 text-rose-600",
  },
  {
    value: "ats",
    label: "ATS Optimizer",
    hint: "Keyword / ATS fit",
    icon: Target,
    accent: "from-sky-500/20 to-sky-500/5 text-sky-600",
  },
  {
    value: "bullets",
    label: "Bullet Transformer",
    hint: "Action · Task · Result",
    icon: PenLine,
    accent: "from-violet-500/20 to-violet-500/5 text-violet-600",
  },
  {
    value: "tone",
    label: "Industry Tone",
    hint: "Tone matching",
    icon: Music2,
    accent: "from-amber-500/20 to-amber-500/5 text-amber-600",
  },
  {
    value: "polish",
    label: "Final Polish",
    hint: "Tense / cliches / quality",
    icon: MicVocal,
    accent: "from-emerald-500/20 to-emerald-500/5 text-emerald-600",
  },
];

const DEFAULT_PROMPTS: Record<string, string> = {
  brutal: "Can you strengthen my weakest sections first?",
  ats: "What keywords am I missing from this job description?",
  bullets: "Rewrite my experience bullets with results and metrics.",
  tone: "Make my summary sound more senior for this industry.",
  polish: "Fix tense inconsistencies and remove cliches.",
};

type StepKey = "review" | "chat" | "apply";

const STEP_ORDER: StepKey[] = ["review", "chat", "apply"];

const STEPS: { key: StepKey; label: string; icon: typeof FileText }[] = [
  { key: "review", label: "Review", icon: FileText },
  { key: "chat", label: "Iterate", icon: MessageSquare },
  { key: "apply", label: "Apply", icon: Rocket },
];

export function CvBuilder() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [reviewType, setReviewType] = useState("full");
  const [industry, setIndustry] = useState("");
  const [jobDescription, setJobDescription] = useState("");

  const [busyReview, setBusyReview] = useState(false);
  const [busyChat, setBusyChat] = useState(false);
  const [busyReady, setBusyReady] = useState(false);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [reviewResults, setReviewResults] = useState<FullReviewResult | null>(null);
  const [resumeText, setResumeText] = useState("");
  const [chatId, setChatId] = useState<string | null>(null);
  const [editSessionId, setEditSessionId] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [canUndo, setCanUndo] = useState(false);
  const [canRedo, setCanRedo] = useState(false);
  const [decision, setDecision] = useState<ApplyDecision | null>(null);
  const [applyResult, setApplyResult] = useState<string | null>(null);

  const [step, setStep] = useState<StepKey>("review");

  const reviewReady = !!reviewResults;
  const iterationReady = !!chatId && !!editSessionId;

  const stepIndex = STEP_ORDER.indexOf(step);
  const isLastStep = stepIndex === STEP_ORDER.length - 1;

  const goTo = (next: StepKey, allowed: boolean) => {
    if (allowed) {
      setError(null);
      setStep(next);
      if (typeof window !== "undefined") window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  const runReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError("Please select a PDF or DOCX resume file");
      return;
    }
    setBusyReview(true);
    setError(null);
    setReviewResults(null);
    setApplyResult(null);
    try {
      const data = await runResumeReview({
        resume: selectedFile,
        reviewType,
        industry,
        jobDescription,
      });
      setReviewResults(data.results as FullReviewResult);
      setResumeText(data.resume_text);
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setBusyReview(false);
    }
  };

  const startChatSession = async (): Promise<boolean> => {
    if (!resumeText || !selectedFile) {
      setError("Run a review first so we can load your resume text.");
      return false;
    }
    setBusyChat(true);
    setError(null);
    try {
      const edit = await createEditSession(selectedFile);
      setEditSessionId(edit.session_id);
      const chat = await startChat(resumeText);
      setChatId(chat.chat_id);
      setChatMessages(chat.history || []);
      return true;
    } catch (err) {
      setError(errMsg(err));
      return false;
    } finally {
      setBusyChat(false);
    }
  };

  const handleSend = async (content: string) => {
    if (!chatId) return;
    setBusyChat(true);
    setError(null);
    const optimistic: ChatMessage = {
      role: "user",
      content,
      id: null,
      created_at: new Date().toISOString(),
    };
    setChatMessages((prev) => [...prev, optimistic]);
    try {
      const data = await sendChatMessage(chatId, content);
      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: data.reply,
        id: null,
        created_at: new Date().toISOString(),
        proposed_edits: data.proposed_edits as ChatProposedEdit[],
      };
      setChatMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setError(errMsg(err));
      setChatMessages((prev) => prev.filter((m) => m !== optimistic));
    } finally {
      setBusyChat(false);
    }
  };

  const handleApplyProposed = async (action: ResumeEditAction) => {
    if (!chatId || !editSessionId) return;
    setBusyChat(true);
    setError(null);
    try {
      const res = await applyChatEdit(chatId, editSessionId, action);
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

  const handleReadiness = async () => {
    if (!chatId || !editSessionId) return;
    setBusyReady(true);
    setError(null);
    setDecision(null);
    try {
      const res = await checkReadiness(chatId, editSessionId, jobDescription || undefined);
      setDecision(res);
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setBusyReady(false);
    }
  };

  const handleApply = async () => {
    if (!chatId || !editSessionId) return;
    setApplying(true);
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
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="space-y-6">
      {error && (
        <Card className="border-destructive/30 bg-destructive/5">
          <CardContent className="p-4 flex items-start gap-2 text-sm text-destructive">
            <AlertCircle size={18} className="mt-0.5 shrink-0" />
            <span>{error}</span>
          </CardContent>
        </Card>
      )}

      {/* Stepper header */}
      <div className="rounded-2xl border border-border/60 bg-card/60 p-4 backdrop-blur">
        <div className="flex items-center justify-between gap-3">
          {STEPS.map((s, i) => {
            const isActive = step === s.key;
            const isDone = STEP_ORDER.indexOf(s.key) < stepIndex;
            const StepIcon = s.icon;
            return (
              <div key={s.key} className="flex flex-1 items-center gap-2">
                <button
                  type="button"
                  onClick={() => goTo(s.key, isDone || isActive)}
                  disabled={!isDone && !isActive}
                  className={`flex items-center gap-2.5 rounded-xl px-2 py-1 text-left transition-all ${
                    isActive
                      ? "bg-primary/10 ring-1 ring-primary/30"
                      : isDone
                      ? "cursor-pointer hover:bg-muted"
                      : "opacity-50 cursor-not-allowed"
                  }`}
                >
                  <span
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold ${
                      isDone
                        ? "bg-emerald-500 text-white"
                        : isActive
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {isDone ? <Check size={15} /> : i + 1}
                  </span>
                  <span className="hidden sm:flex flex-col">
                    <span className={`text-sm font-semibold ${isActive ? "text-foreground" : "text-muted-foreground"}`}>
                      <StepIcon size={13} className="mr-1 inline text-primary" />
                      {s.label}
                    </span>
                    <span className="text-[11px] text-muted-foreground">
                      {s.key === "review" && "Upload & review"}
                      {s.key === "chat" && "Chat + edits"}
                      {s.key === "apply" && "Submit"}
                    </span>
                  </span>
                </button>
                {!isLastStep && i < STEPS.length - 1 && (
                  <div className={`hidden sm:block h-px flex-1 ${isDone ? "bg-emerald-500" : "bg-border"}`} />
                )}
              </div>
            );
          })}
        </div>

        {/* progress bar */}
        <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-muted">
          <div
            className="h-full rounded-full bg-primary transition-all duration-300"
            style={{ width: `${((stepIndex + 1) / STEPS.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Step: Review */}
      {step === "review" && (
        <div className="space-y-5">
          <Card className="border-border/60 bg-card/80 backdrop-blur shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <FileText size={18} className="text-primary" />
                Upload &amp; Review
              </CardTitle>
              <CardDescription>
                Choose your resume, pick a review focus, and (optionally) paste a job description for ATS fit.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={runReview} className="space-y-6">
                <ResumeDropzone
                  selectedFile={selectedFile}
                  dragging={dragging}
                  setDragging={setDragging}
                  onSelectFile={setSelectedFile}
                />

                {/* Review type cards */}
                <div>
                  <Label className="mb-2 block text-sm font-semibold">Review focus</Label>
                  <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                    {REVIEW_TYPES.map((r) => {
                      const selected = reviewType === r.value;
                      const Icon = r.icon;
                      return (
                        <button
                          key={r.value}
                          type="button"
                          onClick={() => setReviewType(r.value)}
                          className={`rounded-xl border p-3 text-left transition-all ${
                            selected
                              ? "border-primary bg-primary/5 ring-1 ring-primary/30"
                              : "border-border/70 hover:border-primary/40 hover:bg-muted/40"
                          }`}
                        >
                          <span className={`mb-1.5 inline-flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br ${r.accent}`}>
                            <Icon size={16} />
                          </span>
                          <span className="block text-sm font-semibold">{r.label}</span>
                          <span className="block text-[11px] text-muted-foreground">{r.hint}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div>
                    <Label className="mb-2 block text-sm font-semibold">
                      Industry <span className="font-normal text-muted-foreground">(for tone, optional)</span>
                    </Label>
                    <Input
                      value={industry}
                      onChange={(e) => setIndustry(e.target.value)}
                      placeholder="e.g. fintech, healthtech"
                    />
                  </div>
                </div>

                {(reviewType === "full" || reviewType === "ats") && (
                  <div>
                    <Label className="mb-2 block text-sm font-semibold">Job Description Text (for ATS)</Label>
                    <Textarea
                      value={jobDescription}
                      onChange={(e) => setJobDescription(e.target.value)}
                      placeholder="Paste the target job description here — used for ATS keyword & fit scoring..."
                      className="min-h-[110px]"
                    />
                  </div>
                )}

                <Separator />

                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-xs text-muted-foreground">
                    {reviewType === "full"
                      ? "Full review runs all 5 agents on structure, ATS keywords, bullets, tone and polish."
                      : `${REVIEW_TYPES.find((r) => r.value === reviewType)?.hint}.`}
                  </p>
                  <Button type="submit" disabled={busyReview || !selectedFile} size="lg" className="gap-2 font-semibold sm:min-w-[160px]">
                    {busyReview ? (
                      <>
                        <RefreshCw className="animate-spin" size={18} />
                        Running review…
                      </>
                    ) : (
                      <>
                        <Sparkles size={18} />
                        Run Review
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {busyReview && (
            <Card className="border-primary/30 bg-primary/5 animate-pulse">
              <CardContent className="p-8 text-center space-y-3">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/20 text-primary">
                  <Sparkles className="animate-spin" size={24} />
                </div>
                <h3 className="text-lg font-semibold">
                  {reviewType === "full" ? "Running 5 review agents…" : "Running review agent…"}
                </h3>
                <p className="text-sm text-muted-foreground">
                  Analyzing structure, ATS keywords, bullets, tone, and polish.
                </p>
              </CardContent>
            </Card>
          )}

          {reviewReady && (
            <div className="space-y-4">
              <CvReviewResults results={reviewResults} />
              <div className="flex items-center justify-end">
                <Button
                  onClick={async () => {
                    const ok = await startChatSession();
                    if (ok) goTo("chat", true);
                  }}
                  disabled={busyChat}
                  className="gap-2"
                >
                  {busyChat ? <RefreshCw className="animate-spin" size={16} /> : <ArrowRight size={16} />}
                  Continue to Iterate
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Step: Iterate */}
      {step === "chat" && (
        <div className="space-y-5">
          <Card className="border-border/60 bg-card/80 backdrop-blur shadow-sm">
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare size={18} className="text-primary" />
                  Chat to refine your CV
                </CardTitle>
                <CardDescription>
                  Ask the assistant to improve bullets, add keywords, or fix tone — then accept edits.
                </CardDescription>
              </div>
              {chatId && (
                <Badge variant="secondary" className="font-mono text-xs">
                  {editSessionId ? "edit session linked" : "no edit session"}
                </Badge>
              )}
            </CardHeader>
            <CardContent>
              {!chatId ? (
                <div className="rounded-xl border border-dashed border-border/80 py-10 text-center">
                  <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                    <MessageSquare size={22} />
                  </div>
                  <p className="mb-1 text-sm font-medium">No chat session yet</p>
                  <p className="mb-4 text-xs text-muted-foreground">
                    Start a session linked to an editable copy of your reviewed resume.
                  </p>
                  <Button onClick={startChatSession} disabled={busyChat} className="gap-2">
                    {busyChat ? <RefreshCw className="animate-spin" size={16} /> : <MessageSquare size={16} />}
                    Start AI Chat Session
                  </Button>
                </div>
              ) : (
                <CvChatPanel
                  messages={chatMessages}
                  busy={busyChat}
                  canUndo={canUndo}
                  canRedo={canRedo}
                  onSend={handleSend}
                  onApplyProposed={handleApplyProposed}
                  onUndo={handleUndo}
                  onRedo={handleRedo}
                  error={error}
                />
              )}
            </CardContent>
          </Card>

          {resumeText && (
            <Card className="border-border/60 bg-card/80 backdrop-blur shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg">Live Resume Text</CardTitle>
                <CardDescription>
                  The edit session's current content. Accepted edits apply here, with undo/redo.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <pre className="max-h-80 overflow-y-auto whitespace-pre-wrap rounded-xl border border-border/40 bg-muted/40 p-4 font-mono text-xs leading-relaxed">
                  {resumeText}
                </pre>
              </CardContent>
            </Card>
          )}

          <div className="space-y-4 rounded-2xl border border-border/60 bg-card/60 p-5">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <CheckCircle2 size={16} className="text-primary" />
                Application readiness
              </div>
              <Button
                onClick={handleReadiness}
                disabled={!iterationReady || busyReady}
                size="sm"
                variant="outline"
                className="gap-2"
              >
                {busyReady ? <RefreshCw className="animate-spin" size={14} /> : <CheckCircle2 size={14} />}
                Check readiness
              </Button>
            </div>
            {decision && (
              <div
                className={`rounded-xl p-4 text-sm ${
                  decision.ready ? "bg-emerald-500/10 text-emerald-700" : "bg-amber-500/10 text-amber-700"
                }`}
              >
                <div className="mb-1 flex items-center gap-2">
                  <Badge variant="secondary" className={decision.ready ? "bg-emerald-500/20 text-emerald-700" : "bg-amber-500/20 text-amber-700"}>
                    {decision.application_status}
                  </Badge>
                  <span className="text-xs font-medium">{decision.ready ? "Ready to apply" : "Needs review"}</span>
                </div>
                <p>{decision.summary}</p>
              </div>
            )}
          </div>

          <div className="flex items-center justify-between">
            <Button variant="ghost" onClick={() => goTo("review", true)} className="gap-2">
              <ArrowLeft size={16} /> Back
            </Button>
            <Button onClick={() => goTo("apply", true)} className="gap-2">
              Continue to Apply <ArrowRight size={16} />
            </Button>
          </div>
        </div>
      )}

      {/* Step: Apply */}
      {step === "apply" && (
        <div className="space-y-5">
          <Card className="border-border/60 bg-card/80 backdrop-blur shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Rocket size={18} className="text-primary" />
                Submit Application
              </CardTitle>
              <CardDescription>
                Storage-only submission for the MVP. The final edited resume is persisted as your application.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-xl border border-border/40 bg-muted/40 p-4 text-sm">
                <p className="mb-0.5 font-semibold">Final resume (from edit session)</p>
                <p className="font-mono text-xs text-muted-foreground">
                  {editSessionId ? `edit_session_id: ${editSessionId}` : "No edit session linked yet"}
                </p>
              </div>
              <div className="flex items-center justify-end gap-3">
                <Button variant="ghost" onClick={() => goTo("chat", true)} className="gap-2">
                  <ArrowLeft size={16} /> Back
                </Button>
                <Button onClick={handleApply} disabled={applying || !editSessionId} size="lg" className="gap-2 font-semibold">
                  {applying ? <RefreshCw className="animate-spin" size={18} /> : <Rocket size={18} />}
                  Submit Application
                </Button>
              </div>
              <p className="flex items-start gap-2 text-sm text-muted-foreground">
                <Sparkles size={16} className="mt-0.5 shrink-0 text-primary" />
                Optional: an external job site auto-apply can be wired by posting the application payload to the provider.
              </p>
            </CardContent>
          </Card>

          {applyResult && (
            <Card className="border-emerald-500/40 bg-emerald-500/5">
              <CardContent className="flex items-start gap-2 p-5 text-emerald-700">
                <CheckCircle2 size={18} className="mt-0.5 shrink-0" />
                <p className="text-sm font-medium">{applyResult}</p>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

export { DEFAULT_PROMPTS };
