import { useState, useRef, useEffect } from "react";
import type { ChatMessage, ResumeEditAction } from "@/shared/types";
import { Button } from "@/shared/components/ui/button";
import { Textarea } from "@/shared/components/ui/textarea";
import { Badge } from "@/shared/components/ui/badge";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { Send, Check, History, RotateCcw, AlertTriangle } from "lucide-react";

export function CvChatPanel({
  messages,
  busy,
  canUndo,
  canRedo,
  onSend,
  onApplyProposed,
  onUndo,
  onRedo,
  error,
}: {
  messages: ChatMessage[];
  busy: boolean;
  canUndo: boolean;
  canRedo: boolean;
  onSend: (content: string) => void;
  onApplyProposed: (edit: ResumeEditAction) => void;
  onUndo: () => void;
  onRedo: () => void;
  error: string | null;
}) {
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const [appliedKey, setAppliedKey] = useState<string | null>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    const content = input.trim();
    if (!content || busy) return;
    setInput("");
    onSend(content);
  };

  return (
    <div className="flex h-full flex-col">
      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto pr-1 min-h-[240px] max-h-[420px]">
        {messages.length === 0 && (
          <div className="text-center text-sm text-muted-foreground py-12">
            <p className="text-lg font-semibold text-foreground mb-1">CV Review Assistant</p>
            <p>Chat to iterate on your resume. Ask to strengthen bullets, add keywords, or fix tone.</p>
          </div>
        )}

        {messages.map((m, msgIdx) => (
          <div key={msgIdx} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                m.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted text-foreground"
              }`}
            >
              <p className="whitespace-pre-wrap">{m.content}</p>

              {m.role === "assistant" && m.proposed_edits && m.proposed_edits.length > 0 && (
                <div className="mt-3 space-y-2 border-t border-border/40 pt-3">
                  <p className="text-xs font-semibold text-muted-foreground">
                    Suggested edits ({m.proposed_edits.length})
                  </p>
                  {m.proposed_edits.map((edit, i) => {
                    const key = `${msgIdx}-${i}`;
                    const isApplied = appliedKey === key;
                    return (
                      <div key={key} className="rounded-xl bg-background/60 border border-border/60 p-2.5">
                        <div className="flex items-center justify-between gap-2">
                          <Badge variant="secondary" className="text-[10px] uppercase">
                            {edit.action_type}
                          </Badge>
                          {edit.text.includes("\n") ? (
                            <span className="text-[11px] text-muted-foreground">
                              {edit.text.split("\n").length} lines
                            </span>
                          ) : (
                            <span className="text-[11px] text-muted-foreground truncate">
                              {edit.text}
                            </span>
                          )}
                        </div>
                        <Button
                          size="sm"
                          variant={isApplied ? "secondary" : "default"}
                          disabled={isApplied || busy}
                          onClick={() => {
                            setAppliedKey(key);
                            onApplyProposed({
                              action_type: edit.action_type as "insert" | "replace" | "delete",
                              start_line: edit.start_line,
                              end_line: edit.end_line,
                              text: edit.text,
                              previous_text: "",
                            });
                          }}
                          className="mt-2 w-full gap-1.5"
                        >
                          {isApplied ? (
                            <>
                              <Check size={14} /> Applied
                            </>
                          ) : (
                            <>
                              <Check size={14} /> Apply to resume
                            </>
                          )}
                        </Button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        ))}

        {busy && (
          <div className="flex justify-start">
            <div className="max-w-[85%] space-y-2 rounded-2xl bg-muted px-4 py-3">
              <Skeleton className="h-3.5 w-48" />
              <Skeleton className="h-3.5 w-64" />
              <Skeleton className="h-3.5 w-40" />
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="my-2 flex items-center gap-2 rounded-xl bg-destructive/10 border border-destructive/30 px-3 py-2 text-xs text-destructive">
          <AlertTriangle size={14} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="mt-3 flex items-center gap-2">
        <Button variant="outline" size="icon" title="Undo" disabled={!canUndo || busy} onClick={onUndo}>
          <History size={16} />
        </Button>
        <Button variant="outline" size="icon" title="Redo" disabled={!canRedo || busy} onClick={onRedo}>
          <RotateCcw size={16} />
        </Button>
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="Ask to improve your resume..."
          rows={1}
          className="flex-1 resize-none"
        />
        <Button onClick={handleSend} disabled={busy || !input.trim()} size="icon">
          <Send size={16} />
        </Button>
      </div>
    </div>
  );
}
