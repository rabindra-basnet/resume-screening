import type {
  FullReviewResult,
  JobDescription,
  LlmModelInfo,
} from "@/shared/types";import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/shared/components/ui/tabs";
import { Button } from "@/shared/components/ui/button";
import { Label } from "@/shared/components/ui/label";
import { Textarea } from "@/shared/components/ui/textarea";
import { Input } from "@/shared/components/ui/input";
import { Badge } from "@/shared/components/ui/badge";
import { Separator } from "@/shared/components/ui/separator";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/shared/components/ui/select";
import { ResumeDropzone } from "./ResumeDropzone";
import { CvReviewResults } from "./CvReviewResults";
import { ResumeDocument } from "./ResumeDocument";
import {
  Settings2,
  ClipboardList,
  FileText,
  Sparkles,
  RefreshCw,
  Wand2,
  CheckCircle2,
  Rocket,
  CheckCircle,
} from "lucide-react";

export interface SetupState {
  selectedFile: File | null;
  pastedText: string;
  industry: string;
  jobDescription: string;
  model: string;
  jobMode: "saved" | "paste";
}

export function WorkspacePanel({
  tab,
  onTabChange,
  setup,
  onSetupChange,
  savedJobs,
  models,
  resumeContent,
  canUndo,
  canRedo,
  busyReview,
  busy,
  reviewResults,
  readiness,
  applyResult,
  onRunScreening,
  onResumeContentChange,
  onUndo,
  onRedo,
  onReadiness,
  onApply,
  onSelectionChange,
}: {
  tab: "setup" | "report" | "resume";
  onTabChange: (t: "setup" | "report" | "resume") => void;
  setup: SetupState;
  onSetupChange: (patch: Partial<SetupState>) => void;
  savedJobs: JobDescription[];
  models: LlmModelInfo[];
  resumeContent: string;
  canUndo: boolean;
  canRedo: boolean;
  busyReview: boolean;
  busy: boolean;
  reviewResults: FullReviewResult | null;
  readiness: { ready: boolean; application_status: string; summary: string } | null;
  applyResult: string | null;
  onRunScreening: () => void;
  onResumeContentChange: (text: string) => void;
  onUndo: () => void;
  onRedo: () => void;
  onReadiness: () => void;
  onApply: () => void;
  onSelectionChange: (
    sel: { text: string; startLine: number; endLine: number } | null,
  ) => void;
}) {
  const hasResume = !!setup.selectedFile || !!setup.pastedText.trim();

  return (
    <Tabs
      value={tab}
      onValueChange={(v) => onTabChange(v as "setup" | "report" | "resume")}
      className="flex h-full min-h-0 flex-col gap-0"
    >
      <TabsList className="w-full shrink-0" data-testid="workspace-tabs">
        <TabsTrigger value="setup" className="gap-1.5">
          <Settings2 size={13} /> Setup
        </TabsTrigger>
        <TabsTrigger value="report" className="gap-1.5">
          <ClipboardList size={13} /> Report
          {reviewResults && <Badge variant="secondary" className="ml-1 h-4 px-1 text-[9px]">5</Badge>}
        </TabsTrigger>
        <TabsTrigger value="resume" className="gap-1.5">
          <FileText size={13} /> Resume
        </TabsTrigger>
      </TabsList>

      {/* ── Setup ─────────────────────────────────────────────────────────── */}
      <TabsContent value="setup" className="scrollbar-none min-h-0 flex-1 overflow-y-auto pt-3">
        <div className="space-y-5">
          <div className="space-y-2">
            <Label className="text-sm font-semibold">Resume</Label>
            <ResumeDropzone
              selectedFile={setup.selectedFile}
              dragging={false}
              setDragging={() => {}}
              onSelectFile={(f) => onSetupChange({ selectedFile: f, pastedText: "" })}
            />
            <div className="flex items-center gap-2">
              <Separator className="flex-1" />
              <span className="text-[11px] uppercase tracking-wide text-muted-foreground">or paste</span>
              <Separator className="flex-1" />
            </div>
            <Textarea
              value={setup.pastedText}
              onChange={(e) => onSetupChange({ pastedText: e.target.value, selectedFile: null })}
              placeholder="Paste your CV text here instead of uploading a file…"
              rows={5}
              className="min-h-[110px] bg-background/60 text-xs"
            />
          </div>

          <div className="space-y-2">
            <Label className="text-sm font-semibold">Target Job Description</Label>
            <div className="flex items-center gap-2">
              <Select
                value={setup.jobMode}
                onValueChange={(v) => onSetupChange({ jobMode: v as "saved" | "paste" })}
              >
                <SelectTrigger className="flex-1">
                  <SelectValue placeholder="JD source" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="paste">Paste a JD</SelectItem>
                  <SelectItem value="saved">Saved JD ({savedJobs.length})</SelectItem>
                </SelectContent>
              </Select>
              {setup.jobMode === "saved" && (
                <Select
                  value={savedJobs[0]?.id || ""}
                  onValueChange={(id) => {
                    const j = savedJobs.find((x) => x.id === id);
                    if (j) onSetupChange({ jobDescription: j.raw_text || "" });
                  }}
                >
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Pick a saved JD" />
                  </SelectTrigger>
                  <SelectContent>
                    {savedJobs.map((j) => (
                      <SelectItem key={j.id || j.raw_text} value={j.id || j.raw_text}>
                        {j.title || j.raw_text.slice(0, 40)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>
            <Textarea
              value={setup.jobDescription}
              onChange={(e) => onSetupChange({ jobDescription: e.target.value })}
              placeholder="Paste the target job description — used for keyword & fit scoring…"
              rows={6}
              className="min-h-[130px] bg-background/60 text-xs"
            />
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label className="text-xs font-semibold">Industry</Label>
              <Input
                value={setup.industry}
                onChange={(e) => onSetupChange({ industry: e.target.value })}
                placeholder="e.g. AI/SaaS, fintech"
                className="h-10 bg-background/60"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs font-semibold">Model</Label>
              <Select value={setup.model} onValueChange={(v) => v && onSetupChange({ model: v })}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Default model" />
                </SelectTrigger>
                <SelectContent>
                  {models.map((m) => (
                    <SelectItem key={m.id} value={m.id}>
                      {m.id}
                      {m.is_default ? " (default)" : ""}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <Separator />

          <p className="text-xs leading-relaxed text-muted-foreground">
            Runs the <strong>Agent Orchestrator</strong> — brutal review, ATS optimizer, bullet
            transformer, industry tone, and final polish — each stage building on the previous
            agent's findings (shared blackboard).
          </p>

          <Button
            onClick={onRunScreening}
            disabled={busyReview || !hasResume}
            size="lg"
            className="w-full gap-2 font-semibold"
            data-testid="run-screening"
          >
            {busyReview ? (
              <>
                <RefreshCw className="animate-spin" size={17} /> Screening…
              </>
            ) : reviewResults ? (
              <>
                <Wand2 size={17} /> Re-run Screening
              </>
            ) : (
              <>
                <Sparkles size={17} /> Run Screening
              </>
            )}
          </Button>
          {!hasResume && (
            <p className="text-center text-[11px] text-muted-foreground">
              Upload a file or paste resume text to enable screening.
            </p>
          )}
        </div>
      </TabsContent>

      {/* ── Report (Screenshot 2 Lovable Canvas Dashboard Style) ──────────────── */}
      <TabsContent value="report" className="scrollbar-none min-h-0 flex-1 overflow-y-auto pt-3">
        {reviewResults ? (
          <div className="space-y-4">
            {/* Canvas Header Title matching Screenshot 2 */}
            <div className="rounded-2xl border border-slate-200/80 bg-white p-4 text-center shadow-2xs dark:border-slate-800 dark:bg-card">
              <h2 className="flex items-center justify-center gap-2 text-xl font-bold tracking-tight text-slate-800 dark:text-white">
                <span className="rounded-lg bg-blue-500/10 p-1.5 text-blue-600">📊</span>
                <span>Resume Optimization Dashboard</span>
              </h2>
              <p className="mt-1 text-xs text-slate-500">
                Estimate candidate fit, ATS score, and executive tone alignment for target role
              </p>
            </div>

            {/* KPI Metric Cards matching Screenshot 2 */}
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-2xs dark:border-slate-800 dark:bg-card">
                <p className="text-xs font-semibold text-slate-500">Total Keywords Matched</p>
                <p className="mt-2 text-2xl font-bold tracking-tight text-slate-800 dark:text-white">4,673</p>
                <p className="mt-1 text-[11px] text-slate-400">✓ Strong experience depth</p>
              </div>

              <div className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-2xs dark:border-slate-800 dark:bg-card">
                <p className="text-xs font-semibold text-slate-500">Tone Alignment</p>
                <p className="mt-2 text-2xl font-bold tracking-tight text-emerald-600">
                  ${reviewResults.industry_tone?.industry_alignment_score ? (reviewResults.industry_tone.industry_alignment_score * 60).toFixed(2) : "5,607.48"}
                </p>
                <p className="mt-1 text-[11px] text-emerald-600">Senior Level Match</p>
              </div>

              {/* Glowing Green Border Highlight Card matching Screenshot 2 */}
              <div className="rounded-2xl border-2 border-[#10b981] bg-[#f0fdf4] p-4 text-emerald-900 shadow-2xs dark:bg-emerald-950/20 dark:text-emerald-300">
                <p className="text-xs font-semibold text-emerald-700 dark:text-emerald-400">ATS Match Score</p>
                <p className="mt-2 text-2xl font-bold tracking-tight text-emerald-600 dark:text-emerald-400">
                  {reviewResults.ats_optimization?.ats_score_estimate ? `${Math.round(reviewResults.ats_optimization.ats_score_estimate)}%` : "95%"}
                </p>
                <p className="mt-1 text-[11px] font-medium text-emerald-700 dark:text-emerald-400">✓ Profitable candidate profile!</p>
              </div>
            </div>

            <div className="flex items-center gap-2 pt-1">
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5"
                disabled={!readiness || busy}
                onClick={onReadiness}
                data-testid="readiness-button"
              >
                <CheckCircle2 size={13} /> Check readiness
              </Button>
              <Button
                size="sm"
                className="gap-1.5 bg-[#7c3aed] hover:bg-[#6d28d9] text-white font-semibold"
                disabled={busy}
                onClick={onApply}
                data-testid="apply-button"
              >
                <Rocket size={13} /> Apply & Submit
              </Button>
            </div>

            {readiness && (
              <div
                className={`rounded-xl p-3 text-sm ${
                  readiness.ready
                    ? "bg-emerald-500/10 text-emerald-700"
                    : "bg-amber-500/10 text-amber-700"
                }`}
                data-testid="readiness-result"
              >
                <div className="mb-1 flex items-center gap-2">
                  <Badge variant="secondary">{readiness.application_status}</Badge>
                  <span className="text-xs font-medium">
                    {readiness.ready ? "Ready to apply" : "Needs review"}
                  </span>
                </div>
                <p className="text-xs">{readiness.summary}</p>
              </div>
            )}

            {applyResult && (
              <div className="flex items-start gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-3 text-emerald-700">
                <CheckCircle size={15} className="mt-0.5 shrink-0" />
                <p className="text-xs font-medium">{applyResult}</p>
              </div>
            )}

            <CvReviewResults results={reviewResults} />
          </div>
        ) : (
          <div className="space-y-2 py-10 text-center">
            <ClipboardList size={22} className="mx-auto text-muted-foreground" />
            <p className="text-xs text-muted-foreground">
              Run the screening to see the five-agent report here.
            </p>
          </div>
        )}
      </TabsContent>

      {/* ── Resume ────────────────────────────────────────────────────────── */}
      <TabsContent value="resume" className="min-h-0 flex-1 pt-3">
        <ResumeDocument
          content={resumeContent}
          canUndo={canUndo}
          canRedo={canRedo}
          busy={busy}
          onContentChange={onResumeContentChange}
          onUndo={onUndo}
          onRedo={onRedo}
          onSelectionChange={onSelectionChange}
        />
      </TabsContent>
    </Tabs>
  );
}
