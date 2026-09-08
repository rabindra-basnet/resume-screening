import { useEffect, useRef, useState } from "react";
import type { ChatMessage, ChatProposedEdit, FullReviewResult } from "@/shared/types";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { CvReviewResults } from "./CvReviewResults";
import { cn } from "@/shared/lib/utils";
import {
  Bot,
  User,
  Check,
  Sparkles,
  ChevronDown,
  ClipboardList,
  TextSelect,
} from "lucide-react";

function AssistantReport({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(true);
  return (
    <div className="mt-3 overflow-hidden rounded-xl border border-border/60 bg-background/60" data-testid="screening-report">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs font-semibold text-muted-foreground transition-colors hover:bg-muted/50"
      >
        <ClipboardList size={13} className="text-primary" />
        Screening report — 5 agents
        <ChevronDown
          size={14}
          className={cn("ml-auto transition-transform", open && "rotate-180")}
        />
      </button>
      {open && <div className="max-h-[420px] overflow-y-auto px-3 pb-3">{children}</div>}
    </div>
  );
}

function ProposedEdits({
  edits,
  busy,
  onApply,
}: {
  edits: ChatProposedEdit[];
  busy: boolean;
  onApply: (edit: ChatProposedEdit) => void;
}) {
  const [appliedKeys, setAppliedKeys] = useState<Set<string>>(new Set());

  return (
    <div className="mt-3 space-y-2 border-t border-border/50 pt-3">
      <p className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground">
        <Sparkles size={12} className="text-primary" />
        Proposed edits ({edits.length})
      </p>
      {edits.map((edit, i) => {
        const key = `${edit.action_type}-${edit.start_line}-${edit.end_line}-${i}`;
        const applied = appliedKeys.has(key);
        return (
          <div key={key} className="space-y-2 rounded-xl border border-border/60 bg-muted/30 p-2.5">
            <div className="flex items-center justify-between gap-2">
              <Badge variant="outline" className="text-[10px] font-mono uppercase">
                {edit.action_type} · L{edit.start_line}–{edit.end_line}
              </Badge>
              {edit.text.includes("\n") && (
                <span className="text-[10px] text-muted-foreground">
                  {edit.text.split("\n").length} lines
                </span>
              )}
            </div>
            <p className="max-h-24 overflow-y-auto whitespace-pre-wrap rounded-lg border border-border/40 bg-background/80 p-2 font-mono text-[11px] leading-relaxed">
              {edit.text}
            </p>
            <Button
              size="sm"
              variant={applied ? "secondary" : "default"}
              disabled={applied || busy}
              className="w-full gap-1.5"
              data-testid={`apply-edit-${i}`}
              onClick={() => {
                setAppliedKeys((prev) => new Set(prev).add(key));
                onApply(edit);
              }}
            >
              {applied ? (
                <>
                  <Check size={13} className="text-emerald-500" /> Applied
                </>
              ) : (
                <>
                  <Check size={13} /> Apply to resume
                </>
              )}
            </Button>
          </div>
        );
      })}
    </div>
  );
}

function AssistantThoughtBlock({
  thoughtTime = "7s",
  editingTarget = "Resume Document",
}: {
  thoughtTime?: string;
  editingTarget?: string;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mb-2 space-y-1">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="inline-flex items-center gap-1.5 rounded-full border border-border/50 bg-muted/40 px-2.5 py-1 text-[11px] font-medium text-muted-foreground transition-colors hover:bg-muted"
      >
        <Sparkles size={11} className="text-amber-500" />
        <span>Thought for {thoughtTime}</span>
        <ChevronDown size={11} className={cn("transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <div className="rounded-xl border border-border/40 bg-muted/20 p-2.5 text-[11px] leading-relaxed text-muted-foreground">
          <p className="font-semibold text-foreground">5-Agent Blackboard Trace:</p>
          <ul className="mt-1 space-y-1 list-disc pl-4">
            <li><strong>BrutalReviewAgent:</strong> Scored candidate alignment and experience depth.</li>
            <li><strong>ATSOptimizerAgent:</strong> Cross-referenced target JD requirements and extracted keywords.</li>
            <li><strong>BulletTransformerAgent:</strong> Reformatted experience metrics with Action-Task-Result structure.</li>
            <li><strong>IndustryToneMatchAgent:</strong> Adapted executive tone for target sector.</li>
          </ul>
        </div>
      )}

      {editingTarget && (
        <div className="flex items-center gap-1.5 text-[11px] font-medium text-muted-foreground">
          <TextSelect size={11} className="text-primary" />
          <span>Editing <code className="rounded bg-muted px-1 font-mono text-[10px] text-foreground">{editingTarget}</code></span>
        </div>
      )}
    </div>
  );
}

export function ChatMessages({
  messages,
  reviewResults,
  busy,
  statusText,
  selection,
  onApplyProposed,
  hasResume,
}: {
  messages: ChatMessage[];
  reviewResults: FullReviewResult | null;
  busy: boolean;
  statusText?: string | null;
  selection: { text: string; startLine: number; endLine: number } | null;
  onApplyProposed: (edit: ChatProposedEdit) => void;
  hasResume: boolean;
}) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages.length, busy]);

  return (
    <div ref={scrollRef} className="scrollbar-none min-h-0 flex-1 space-y-4 overflow-y-auto px-1 py-2" data-testid="chat-messages">
      {messages.length === 0 && !busy && (
        <div className="mx-auto max-w-md space-y-3 py-10 text-center" data-testid="chat-empty-state">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
            <Bot size={24} />
          </div>
          <h3 className="text-base font-semibold">Your screening assistant</h3>
          <p className="text-xs leading-relaxed text-muted-foreground">
            {hasResume
              ? "Ask for rewrites, missing ATS keywords, or tone fixes. Select any part of the resume on the right and the assistant will target exactly those lines."
              : "Upload a resume or paste text in Setup, then run the screening. The agents' report lands here and the chat opens for iteration."}
          </p>
        </div>
      )}

      {messages.map((m, idx) => {
        const isLast = idx === messages.length - 1;
        return (
          <div
            key={`msg-${idx}`}
            className={cn("flex gap-2.5", m.role === "user" ? "justify-end" : "justify-start")}
          >
            {m.role === "assistant" && (
              <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-primary/20 bg-primary/10 text-primary">
                <Bot size={14} />
              </div>
            )}

            <div
              className={cn(
                "max-w-[85%] space-y-1 rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-2xs",
                m.role === "user"
                  ? "rounded-tr-2xs bg-primary text-primary-foreground"
                  : "rounded-tl-2xs border border-border/60 bg-card text-foreground",
              )}
            >
              {m.role === "user" && selection && (
                <div className="mb-1.5 flex items-center gap-1.5 rounded-lg bg-primary-foreground/15 px-2 py-1 text-[11px]">
                  <TextSelect size={11} />
                  Targeting resume lines {selection.startLine}–{selection.endLine}
                </div>
              )}

              {m.role === "assistant" && (
                <AssistantThoughtBlock
                  thoughtTime={`${Math.min(7 + idx * 2, 12)}s`}
                  editingTarget={m.proposed_edits && m.proposed_edits.length > 0 ? "resume.txt" : undefined}
                />
              )}

              <p className="whitespace-pre-wrap">{m.content}</p>

              {m.role === "assistant" && isLast && reviewResults && (
                <AssistantReport>
                  <CvReviewResults results={reviewResults} />
                </AssistantReport>
              )}

              {m.role === "assistant" &&
                m.proposed_edits &&
                m.proposed_edits.length > 0 && (
                  <ProposedEdits edits={m.proposed_edits} busy={busy} onApply={onApplyProposed} />
                )}
            </div>

            {m.role === "user" && (
              <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-border/40 bg-muted text-muted-foreground">
                <User size={14} />
              </div>
            )}
          </div>
        );
      })}

      {busy && (
        <div className="flex gap-2.5" data-testid="chat-busy-indicator">
          <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-primary/30 bg-primary/10 text-primary">
            <Bot size={14} className="animate-spin text-primary" />
          </div>
          <div className="w-full max-w-[85%] space-y-2 rounded-2xl rounded-tl-2xs border border-primary/30 bg-card p-3.5 shadow-sm">
            <div className="flex items-center justify-between gap-2 border-b border-border/40 pb-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-primary">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
                </span>
                <span>Live Generative Stream Active</span>
              </div>
              <span className="font-mono text-[10px] text-muted-foreground">5 AGENTS</span>
            </div>

            <p className="text-xs font-medium text-foreground">{statusText || "Agents analyzing & rewriting document…"}</p>

            <div className="space-y-1 pt-1">
              <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                <div className="h-full w-2/3 animate-pulse rounded-full bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500" />
              </div>
              <div className="flex justify-between font-mono text-[9px] text-muted-foreground">
                <span>BrutalReview → ATS → Bullet → Tone → Polish</span>
                <span className="animate-pulse text-emerald-500">Streaming edits live…</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
