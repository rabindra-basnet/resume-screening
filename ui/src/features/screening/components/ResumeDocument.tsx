import { useEffect, useRef, useState } from "react";
import {
  FileText,
  Pencil,
  Check,
  X,
  Undo2,
  Redo2,
  Sparkles,
  TextSelect,
} from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { Badge } from "@/shared/components/ui/badge";
import { cn } from "@/shared/lib/utils";

/**
 * Editable, selectable resume document.
 *
 * - Direct editing: user toggles edit mode and types; changes flow back through
 *   the parent (`onContentChange`) and are the source for chat/apply operations.
 * - AI selection targeting: when the user selects text while NOT editing, the
 *   selection (with its line range) is surfaced so the AI can update exactly
 *   that part ("rewrite only what I highlighted").
 */
export function ResumeDocument({
  content,
  canUndo,
  canRedo,
  busy,
  onContentChange,
  onUndo,
  onRedo,
  onSelectionChange,
}: {
  content: string;
  canUndo: boolean;
  canRedo: boolean;
  busy: boolean;
  onContentChange: (text: string) => void;
  onUndo: () => void;
  onRedo: () => void;
  onSelectionChange: (selection: { text: string; startLine: number; endLine: number } | null) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(content);
  const [selection, setSelection] = useState<{ text: string; startLine: number; endLine: number } | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const displayRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    if (!editing) setDraft(content);
  }, [content, editing]);

  // Compute line numbers of the current text selection inside the document.
  const captureSelection = () => {
    if (editing) return;
    const selectionObj = window.getSelection();
    const node = selectionObj?.anchorNode;
    if (!selectionObj || selectionObj.isCollapsed || !node || !displayRef.current) {
      setSelection(null);
      onSelectionChange(null);
      return;
    }
    if (!displayRef.current.contains(node)) {
      setSelection(null);
      onSelectionChange(null);
      return;
    }
    const text = selectionObj.toString();
    if (!text.trim()) {
      setSelection(null);
      onSelectionChange(null);
      return;
    }
    const start = selectionObj.getRangeAt(0).cloneRange();
    const pre = document.createRange();
    pre.selectNodeContents(displayRef.current);
    pre.setEnd(start.startContainer, start.startOffset);
    const before = pre.toString();
    const startLine = before ? before.split("\n").length : 1;
    const endLine = startLine + (text.split("\n").length - 1);
    setSelection({ text, startLine, endLine });
    onSelectionChange({ text, startLine, endLine });
  };

  const startEditing = () => {
    setDraft(content);
    setEditing(true);
    requestAnimationFrame(() => textareaRef.current?.focus());
  };

  const commitDraft = () => {
    setEditing(false);
    if (draft !== content) onContentChange(draft.trim());
  };

  const cancelDraft = () => {
    setDraft(content);
    setEditing(false);
  };

  const lines = content ? content.split("\n").length : 0;

  return (
    <div className="flex h-full min-h-0 flex-col gap-2" data-testid="resume-document">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <FileText size={15} className="text-primary" />
          <span className="text-sm font-semibold">Resume document</span>
          <Badge variant="secondary" className="text-[10px] font-mono">
            {lines} lines
          </Badge>
          {busy && (
            <Badge variant="secondary" className="animate-pulse text-[10px]">
              syncing…
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            title="Undo edit"
            disabled={!canUndo || busy}
            onClick={onUndo}
          >
            <Undo2 size={14} />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            title="Redo edit"
            disabled={!canRedo || busy}
            onClick={onRedo}
          >
            <Redo2 size={14} />
          </Button>
          {editing ? (
            <>
              <Button variant="ghost" size="icon" title="Cancel" onClick={cancelDraft}>
                <X size={14} />
              </Button>
              <Button size="sm" className="gap-1.5" onClick={commitDraft} data-testid="save-resume">
                <Check size={13} /> Save
              </Button>
            </>
          ) : (
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5"
              onClick={startEditing}
              data-testid="edit-resume"
              disabled={!content}
            >
              <Pencil size={13} /> Edit
            </Button>
          )}
        </div>
      </div>

      {selection && !editing && (
        <div
          data-testid="selection-banner"
          className="flex items-start gap-2 rounded-xl border border-primary/30 bg-primary/5 px-3 py-2 text-xs text-foreground"
        >
          <TextSelect size={14} className="mt-0.5 shrink-0 text-primary" />
          <div className="min-w-0 flex-1">
            <span className="font-semibold">Lines {selection.startLine}–{selection.endLine} selected. </span>
            <span className="text-muted-foreground">
              Ask the assistant to rewrite exactly this part — the selection is attached to your next message.
            </span>
          </div>
          <button
            type="button"
            aria-label="Clear selection"
            className="shrink-0 rounded-md p-0.5 text-muted-foreground hover:text-foreground"
            onClick={() => {
              window.getSelection()?.removeAllRanges();
              setSelection(null);
              onSelectionChange(null);
            }}
          >
            <X size={13} />
          </button>
        </div>
      )}

      {editing ? (
        <textarea
          ref={textareaRef}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          spellCheck={false}
          data-testid="resume-textarea"
          className="scrollbar-none min-h-0 w-full flex-1 resize-none rounded-xl border border-primary/40 bg-background p-3.5 font-mono text-xs leading-relaxed shadow-inner outline-none focus:ring-2 focus:ring-ring/40"
        />
      ) : (
        <pre
          ref={displayRef}
          onMouseUp={captureSelection}
          onTouchEnd={captureSelection}
          data-testid="resume-content"
          className={cn(
            "scrollbar-none min-h-0 flex-1 cursor-text select-text overflow-y-auto whitespace-pre-wrap rounded-xl border border-border/60 bg-background/70 p-3.5 font-mono text-xs leading-relaxed",
            !content && "text-muted-foreground",
          )}
        >
          {content || "Run a screening first — your parsed resume appears here, editable and selectable."}
        </pre>
      )}

      {!editing && content && !selection && (
        <p className="flex items-center gap-1.5 px-1 text-[10px] text-muted-foreground">
          <Sparkles size={11} className="text-primary" />
          Tip: select any lines, then tell the assistant what to change — or click Edit to type directly.
        </p>
      )}
    </div>
  );
}
