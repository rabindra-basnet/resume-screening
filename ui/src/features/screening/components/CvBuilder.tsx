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
  Check,
  Target,
  ListChecks,
  Wrench,
  LineChart,
  GraduationCap,
  Layers,
  Bot,
  AlertTriangle,
  PenTool,
  Mic,
  Star,
} from "lucide-react";



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
  const [reviewType] = useState("full");
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
      <div className="rounded-2xl border border-border/80 bg-card/80 p-4 shadow-xs backdrop-blur">
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

      {/* Workspace Layout: two-column on desktop, stacked on mobile */}
      <div className="space-y-8">
        {step === "review" && (
          <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-[minmax(0,1.8fr)_minmax(360px,1fr)]">
            {/* LEFT: Resume upload + status + instructions */}
            <div className="space-y-6">
              <Card className="border-border/80 bg-card/90 backdrop-blur shadow-xs hover:shadow-sm transition-shadow">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <FileText size={18} className="text-primary" />
                    Upload &amp; Review
                  </CardTitle>
                  <CardDescription>
                    Drop your resume to start the multi-agent screening evaluation.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ResumeDropzone
                    selectedFile={selectedFile}
                    dragging={dragging}
                    setDragging={setDragging}
                    onSelectFile={setSelectedFile}
                  />
                </CardContent>
              </Card>

              {/* Resume status / next steps when a file is selected */}
              {selectedFile ? (
                <Card className="border-border/80 bg-card/90 backdrop-blur shadow-xs">
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <ListChecks size={16} className="text-primary" />
                      Resume Status
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <CheckCircle2 size={15} className="text-emerald-500 shrink-0" />
                      <span className="font-medium text-foreground">{selectedFile.name}</span>
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      Configure the target industry and job description on the right, then run the
                      pipeline to analyze ATS fit, structure, skills, and tone.
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <Card className="border-border/80 bg-card/90 backdrop-blur shadow-xs">
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Layers size={16} className="text-primary" />
                      What gets analyzed
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {[
                      { icon: Target, label: "ATS compatibility" },
                      { icon: FileText, label: "Resume structure" },
                      { icon: ListChecks, label: "Skill alignment" },
                      { icon: LineChart, label: "Job-description match" },
                      { icon: Wrench, label: "Missing skills" },
                      { icon: GraduationCap, label: "Improvement tips" },
                    ].map((item) => (
                      <div
                        key={item.label}
                        className="flex items-center gap-2 rounded-xl border border-border/60 bg-muted/30 px-3 py-2 text-sm"
                      >
                        <item.icon size={15} className="text-primary shrink-0" />
                        <span className="text-muted-foreground">{item.label}</span>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}
            </div>

            {/* RIGHT: Review configuration */}
            <Card className="border-border/80 bg-card/90 backdrop-blur shadow-xs hover:shadow-sm transition-shadow">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Bot size={18} className="text-primary" />
                  Review Configuration
                </CardTitle>
                <CardDescription>
                  Target details consumed by the agent pipeline.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={runReview} className="space-y-5">
                  <div className="space-y-4">
                    <div>
                      <Label className="mb-2 block text-sm font-semibold">
                        Target Industry <span className="font-normal text-muted-foreground">(optional)</span>
                      </Label>
                      <Input
                        value={industry}
                        onChange={(e) => setIndustry(e.target.value)}
                        placeholder="e.g. fintech, healthtech, AI/SaaS"
                        className="h-11 border-border/80 bg-background/50 focus:bg-background transition-colors"
                      />
                    </div>

                    <div>
                      <Label className="mb-2 block text-sm font-semibold">Job Description Text (for ATS &amp; Fit)</Label>
                      <Textarea
                        value={jobDescription}
                        onChange={(e) => setJobDescription(e.target.value)}
                        placeholder="Paste the target job description here — consumed by the agent pipeline for keyword and fit scoring..."
                        className="min-h-[180px] border-border/80 bg-background/50 focus:bg-background transition-colors"
                      />
                    </div>
                  </div>

                  <Separator />

                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Runs the <strong>Agent Orchestrator</strong> — structural, ATS, bullet, tone, and
                    quality evaluations in parallel.
                  </p>

                  <Button
                    type="submit"
                    disabled={busyReview || !selectedFile}
                    size="lg"
                    className="w-full gap-2 font-semibold shadow-xs"
                  >
                    {busyReview ? (
                      <>
                        <RefreshCw className="animate-spin" size={18} />
                        Orchestrating Agents…
                      </>
                    ) : (
                      <>
                        <Sparkles size={18} />
                        Run Agent Review Pipeline
                      </>
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>
        )}

        {step === "chat" && (
          <Card className="border-border/60 bg-card/80 backdrop-blur shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare size={18} className="text-primary" />
                Agent Interactive Controls
              </CardTitle>
              <CardDescription>
                Instruct the agent to apply automated edits, check application readiness, or undo previous revisions.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="space-y-3 rounded-xl border border-border/60 bg-muted/30 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2 text-sm font-semibold">
                      <CheckCircle2 size={16} className="text-primary" />
                      Application Readiness
                    </div>
                    <Button
                      onClick={handleReadiness}
                      disabled={!iterationReady || busyReady}
                      size="sm"
                      variant="outline"
                      className="gap-2"
                    >
                      {busyReady ? <RefreshCw className="animate-spin" size={14} /> : <CheckCircle2 size={14} />}
                      Check Readiness
                    </Button>
                  </div>
                  {decision && (
                    <div
                      className={`rounded-xl p-3 text-sm ${
                        decision.ready ? "bg-emerald-500/10 text-emerald-700" : "bg-amber-500/10 text-amber-700"
                      }`}
                    >
                      <div className="mb-1 flex items-center gap-2">
                        <Badge variant="secondary" className={decision.ready ? "bg-emerald-500/20 text-emerald-700" : "bg-amber-500/20 text-amber-700"}>
                          {decision.application_status}
                        </Badge>
                        <span className="text-xs font-medium">{decision.ready ? "Ready to apply" : "Needs review"}</span>
                      </div>
                      <p className="text-xs">{decision.summary}</p>
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between pt-2">
                  <Button variant="ghost" onClick={() => goTo("review", true)} className="gap-2">
                    <ArrowLeft size={16} /> Back to Review
                  </Button>
                  <Button onClick={() => goTo("apply", true)} className="gap-2">
                    Continue to Apply <ArrowRight size={16} />
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {step === "apply" && (
            <Card className="border-border/60 bg-card/80 backdrop-blur shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Rocket size={18} className="text-primary" />
                  Submit Application
                </CardTitle>
                <CardDescription>
                  Save and register your finalized agent-edited resume.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="rounded-xl border border-border/40 bg-muted/40 p-4 text-sm">
                  <p className="mb-0.5 font-semibold">Final Session Status</p>
                  <p className="font-mono text-xs text-muted-foreground">
                    {editSessionId ? `edit_session_id: ${editSessionId}` : "No edit session linked yet"}
                  </p>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <Button variant="ghost" onClick={() => goTo("chat", true)} className="gap-2">
                    <ArrowLeft size={16} /> Back to Chat
                  </Button>
                  <Button onClick={handleApply} disabled={applying || !editSessionId} size="lg" className="gap-2 font-semibold">
                    {applying ? <RefreshCw className="animate-spin" size={18} /> : <Rocket size={18} />}
                    Submit Application
                  </Button>
                </div>
                {applyResult && (
                  <Card className="border-emerald-500/40 bg-emerald-500/5">
                    <CardContent className="flex items-start gap-2 p-4 text-emerald-700">
                      <CheckCircle2 size={18} className="mt-0.5 shrink-0" />
                      <p className="text-sm font-medium">{applyResult}</p>
                    </CardContent>
                  </Card>
                )}
              </CardContent>
            </Card>
          )}

        {/* Bottom Section: Agent Results & Feedback (Positioned below the form) */}
        <div className="w-full space-y-6">
          {busyReview && (
            <Card className="border-primary/30 bg-primary/5 animate-pulse">
              <CardContent className="p-12 text-center space-y-4">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/20 text-primary">
                  <Sparkles className="animate-spin" size={28} />
                </div>
                <h3 className="text-xl font-semibold">
                  Orchestrating 5 Screening Agents…
                </h3>
                <p className="text-sm text-muted-foreground max-w-md mx-auto">
                  The Agent Orchestrator is running Brutal Review, ATS Optimizer, Bullet Transformer, Industry Tone, and Final Quality Polish concurrently.
                </p>
              </CardContent>
            </Card>
          )}

          {step === "review" && reviewReady && (
            <div className="space-y-4">
              <div className="flex items-center justify-between bg-card/60 p-4 rounded-xl border border-border/60 backdrop-blur">
                <div>
                  <h3 className="font-semibold text-base">Agent Orchestrator Results</h3>
                  <p className="text-xs text-muted-foreground">Comprehensive multi-agent evaluation output</p>
                </div>
                <Button
                  onClick={async () => {
                    const ok = await startChatSession();
                    if (ok) goTo("chat", true);
                  }}
                  disabled={busyChat}
                  className="gap-2"
                >
                  {busyChat ? <RefreshCw className="animate-spin" size={16} /> : <ArrowRight size={16} />}
                  Iterate via AI Chat
                </Button>
              </div>
              <CvReviewResults results={reviewResults} />
            </div>
          )}

          {step === "review" && !reviewReady && !busyReview && (
            <Card className="border-dashed border-border/80 bg-card/40">
              <CardContent className="px-6 py-14 text-center space-y-5">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-primary/10 text-primary">
                  <Sparkles size={30} />
                </div>
                <div className="space-y-1.5">
                  <h3 className="text-xl font-semibold">Agent Feedback Pipeline Ready</h3>
                  <p className="text-sm text-muted-foreground max-w-md mx-auto leading-relaxed">
                    Upload a PDF/DOCX resume above to start the multi-agent screening evaluation.
                    Results will appear right here.
                  </p>
                </div>
                <div className="mx-auto grid max-w-2xl grid-cols-1 gap-2 sm:grid-cols-5">
                  {[
                    { icon: AlertTriangle, label: "Brutal Review" },
                    { icon: Target, label: "ATS Optimizer" },
                    { icon: PenTool, label: "Bullet Transformer" },
                    { icon: Mic, label: "Tone Matcher" },
                    { icon: Star, label: "Final Polish" },
                  ].map((agent) => (
                    <div
                      key={agent.label}
                      className="flex items-center gap-2 rounded-xl border border-border/50 bg-muted/40 px-3 py-2.5 sm:flex-col sm:gap-1.5 sm:py-3 sm:text-center"
                    >
                      <agent.icon size={16} className="text-primary shrink-0" />
                      <span className="text-xs font-medium text-muted-foreground">{agent.label}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {step === "chat" && (
            <div className="space-y-6">
              <Card className="border-border/60 bg-card/80 backdrop-blur shadow-sm">
                <CardHeader className="flex-row items-center justify-between space-y-0">
                  <div>
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <MessageSquare size={18} className="text-primary" />
                      Chat to refine your CV
                    </CardTitle>
                    <CardDescription>
                      Instruct the agent to rewrite bullets, optimize keywords, or modify tone.
                    </CardDescription>
                  </div>
                  {chatId && (
                    <Badge variant="secondary" className="font-mono text-xs">
                      {editSessionId ? "session linked" : "no session"}
                    </Badge>
                  )}
                </CardHeader>
                <CardContent>
                  {!chatId ? (
                    <div className="rounded-xl border border-dashed border-border/80 py-12 text-center">
                      <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                        <MessageSquare size={22} />
                      </div>
                      <p className="mb-1 text-sm font-medium">No chat session active</p>
                      <p className="mb-4 text-xs text-muted-foreground">
                        Start an AI session bound to your uploaded resume text.
                      </p>
                      <Button onClick={startChatSession} disabled={busyChat} className="gap-2">
                        {busyChat ? <RefreshCw className="animate-spin" size={16} /> : <MessageSquare size={16} />}
                        Start Agent Session
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
                    <CardTitle className="text-base">Live Resume Text Preview</CardTitle>
                    <CardDescription>
                      Real-time text representation updated after agent revisions.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <pre className="max-h-[420px] overflow-y-auto whitespace-pre-wrap rounded-xl border border-border/40 bg-muted/40 p-4 font-mono text-xs leading-relaxed">
                      {resumeText}
                    </pre>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {step === "apply" && (
            <Card className="border-border/60 bg-card/80 backdrop-blur shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">Final Resume Preview</CardTitle>
                <CardDescription>
                  Review the finalized text prior to persistence.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <pre className="max-h-96 overflow-y-auto whitespace-pre-wrap rounded-xl border border-border/40 bg-muted/40 p-4 font-mono text-xs leading-relaxed">
                  {resumeText || "No resume text available. Please complete step 1 (Review) and step 2 (Iterate)."}
                </pre>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

export { DEFAULT_PROMPTS };
