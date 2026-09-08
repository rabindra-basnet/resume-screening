import { useState, useRef } from "react";
import { SendHorizontal, Zap, Target, PenTool, Wrench, Paperclip, Globe, Lightbulb, Mic, Undo2, Redo2 } from "lucide-react";
import { Textarea } from "@/shared/components/ui/textarea";
import { Button } from "@/shared/components/ui/button";

const QUICK_PROMPTS = [
  { label: "Optimize Resume", prompt: "Run full 5-agent optimization on my resume against target role.", icon: Zap },
  { label: "Analyze ATS Gaps", prompt: "What exact keywords am I missing from the job description?", icon: Target },
  { label: "Senior Tone", prompt: "Make my summary and bullets sound more senior for this industry.", icon: PenTool },
  { label: "Bullet Transformer", prompt: "Rewrite my experience bullets using Action + Task + Result.", icon: Wrench },
];

export function ChatComposer({
  busy,
  canUndo,
  canRedo,
  hasSelection,
  onSend,
  onUndo,
  onRedo,
  onAttachFile,
}: {
  busy: boolean;
  canUndo: boolean;
  canRedo: boolean;
  hasSelection: boolean;
  onSend: (content: string) => void;
  onUndo: () => void;
  onRedo: () => void;
  onAttachFile?: (file: File) => void;
}) {
  const [input, setInput] = useState("");
  const [searchActive, setSearchActive] = useState(false);
  const [reasonActive, setReasonActive] = useState(true);
  const [isRecording, setIsRecording] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const send = (text?: string) => {
    const content = (text ?? input).trim();
    if (!content || busy) return;
    setInput("");
    onSend(content);
  };

  const handleVoiceToggle = () => {
    setIsRecording((prev) => !prev);
    if (!isRecording) {
      setInput((prev) => (prev ? `${prev} [Voice Input]` : "Analyze my resume line by line and optimize tone for Senior level."));
    }
  };

  return (
    <div className="space-y-2.5" data-testid="chat-composer">
      {/* Quick Prompts Chips */}
      <div className="scrollbar-none flex items-center gap-1.5 overflow-x-auto pb-0.5">
        {QUICK_PROMPTS.map((qp) => {
          const Icon = qp.icon;
          return (
            <button
              key={qp.label}
              type="button"
              disabled={busy}
              onClick={() => send(qp.prompt)}
              className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-border/80 bg-card/80 px-3 py-1.5 text-xs font-medium text-muted-foreground transition-all hover:border-primary/50 hover:bg-primary/5 hover:text-primary disabled:opacity-50 shadow-2xs"
            >
              <Icon size={12} className="text-primary" />
              {qp.label}
            </button>
          );
        })}
      </div>

      {/* Main Composer Box with Integrated Action Pills */}
      <div className="relative rounded-2xl border border-border/70 bg-card p-2.5 shadow-sm transition-all focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/20">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f && onAttachFile) onAttachFile(f);
          }}
        />

        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          rows={1}
          placeholder={
            hasSelection
              ? "Describe the change for selected resume lines…"
              : "Ask anything or paste job description..."
          }
          className="max-h-32 min-h-11 w-full resize-none border-none bg-transparent px-1 py-1 text-sm shadow-none focus-visible:ring-0"
          data-testid="chat-input"
        />

        {/* Action Bar Pills (Attach, Search, Reason, Voice/Send) */}
        <div className="mt-2 flex items-center justify-between gap-2 border-t border-border/40 pt-2">
          <div className="flex items-center gap-1.5 overflow-x-auto">
            <button
              type="button"
              disabled={busy}
              onClick={() => fileInputRef.current?.click()}
              className="inline-flex items-center gap-1.5 rounded-full border border-border/60 bg-muted/50 px-2.5 py-1 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground disabled:opacity-50"
            >
              <Paperclip size={12} />
              <span>Attach</span>
            </button>

            <button
              type="button"
              disabled={busy}
              onClick={() => setSearchActive((v) => !v)}
              className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors ${
                searchActive
                  ? "border-primary/50 bg-primary/10 text-primary"
                  : "border-border/60 bg-muted/50 text-muted-foreground hover:bg-muted"
              }`}
            >
              <Globe size={12} />
              <span>Search</span>
            </button>

            <button
              type="button"
              disabled={busy}
              onClick={() => setReasonActive((v) => !v)}
              className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors ${
                reasonActive
                  ? "border-primary/50 bg-primary/10 text-primary"
                  : "border-border/60 bg-muted/50 text-muted-foreground hover:bg-muted"
              }`}
            >
              <Lightbulb size={12} className={reasonActive ? "text-amber-500 fill-amber-500/20" : ""} />
              <span>Reason</span>
            </button>
          </div>

          <div className="flex items-center gap-1.5">
            {onUndo && (
              <Button variant="ghost" size="icon" className="h-8 w-8" title="Undo" disabled={!canUndo || busy} onClick={onUndo}>
                <Undo2 size={13} />
              </Button>
            )}
            {onRedo && (
              <Button variant="ghost" size="icon" className="h-8 w-8" title="Redo" disabled={!canRedo || busy} onClick={onRedo}>
                <Redo2 size={13} />
              </Button>
            )}

            <button
              type="button"
              onClick={handleVoiceToggle}
              className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold text-white transition-transform active:scale-95 ${
                isRecording ? "bg-red-500 animate-pulse" : "bg-orange-500 hover:bg-orange-600 shadow-xs"
              }`}
            >
              <Mic size={13} />
              <span>{isRecording ? "Listening…" : "Voice"}</span>
            </button>

            <Button
              size="icon"
              className="h-8 w-8 rounded-full"
              disabled={busy || !input.trim()}
              onClick={() => send()}
              data-testid="chat-send"
            >
              <SendHorizontal size={14} />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

