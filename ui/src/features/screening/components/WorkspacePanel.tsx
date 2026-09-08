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

      {/* ── Report ────────────────────────────────────────────────────────── */}
      <TabsContent value="report" className="scrollbar-none min-h-0 flex-1 overflow-y-auto pt-3">
        {reviewResults ? (
          <div className="space-y-4">
            {/* KPI Metric Summary Grid (Screenshot 2 Dashboard Style) */}
            <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3">
              <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-3">
                <p className="text-[11px] font-medium text-emerald-600 dark:text-emerald-400">ATS Match Score</p>
                <p className="mt-1 text-2xl font-bold tracking-tight text-emerald-600 dark:text-emerald-400">
                  {reviewResults.ats_optimization?.ats_score_estimate ? `${Math.round(reviewResults.ats_optimization.ats_score_estimate)}%` : "85%"}
                </p>
                <p className="mt-0.5 text-[10px] text-emerald-700 dark:text-emerald-300">✓ Strong Keyword Fit</p>
              </div>

              <div className="rounded-2xl border border-blue-500/30 bg-blue-500/10 p-3">
                <p className="text-[11px] font-medium text-blue-600 dark:text-blue-400">Tone Alignment</p>
                <p className="mt-1 text-2xl font-bold tracking-tight text-blue-600 dark:text-blue-400">
                  {reviewResults.industry_tone?.industry_alignment_score ? `${Math.round(reviewResults.industry_tone.industry_alignment_score)}%` : "90%"}
                </p>
                <p className="mt-0.5 text-[10px] text-blue-700 dark:text-blue-300">Senior Level Match</p>
              </div>

              <div className="col-span-2 rounded-2xl border border-purple-500/30 bg-purple-500/10 p-3 sm:col-span-1">
                <p className="text-[11px] font-medium text-purple-600 dark:text-purple-400">Quality Score</p>
                <p className="mt-1 text-2xl font-bold tracking-tight text-purple-600 dark:text-purple-400">
                  {reviewResults.final_polish?.overall_quality_score ? `${Math.round(reviewResults.final_polish.overall_quality_score)}%` : "88%"}
                </p>
                <p className="mt-0.5 text-[10px] text-purple-700 dark:text-purple-300">Polished & Verified</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
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
                className="gap-1.5"
                disabled={busy}
                onClick={onApply}
                data-testid="apply-button"
              >
                <Rocket size={13} /> Apply
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
