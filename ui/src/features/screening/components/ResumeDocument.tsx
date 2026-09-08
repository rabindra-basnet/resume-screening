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
  Download,
  Eye,
  FileCode,
  FileType,
  FileDown,
} from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { Badge } from "@/shared/components/ui/badge";
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
} from "@/shared/components/ui/select";
import { cn } from "@/shared/lib/utils";

export function ResumeDocument({
  content,
  canUndo,
  canRedo,
  busy,
  fileFormat = "PDF / DOCX",
  onContentChange,
  onUndo,
  onRedo,
  onSelectionChange,
}: {
  content: string;
  canUndo: boolean;
  canRedo: boolean;
  busy: boolean;
  fileFormat?: string;
  onContentChange: (text: string) => void;
  onUndo: () => void;
  onRedo: () => void;
  onSelectionChange: (selection: { text: string; startLine: number; endLine: number } | null) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [viewMode, setViewMode] = useState<"preview" | "raw">("preview");
  const [draft, setDraft] = useState(content);
  const [selection, setSelection] = useState<{ text: string; startLine: number; endLine: number } | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const displayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!editing) setDraft(content);
  }, [content, editing]);

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

  // Export functions for PDF, DOCX, TXT, MD formats
  const handleExport = (format: "txt" | "md" | "pdf" | "docx") => {
    if (!content) return;
    const filename = `Optimized_Resume.${format}`;

    if (format === "pdf") {
      const printWindow = window.open("", "_blank");
      if (printWindow) {
        printWindow.document.write(`
          <html>
            <head>
              <title>${filename}</title>
              <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; line-height: 1.6; color: #1a1a1a; }
                h1, h2, h3 { color: #0f172a; border-bottom: 1px solid #e2e8f0; pb: 4px; }
                pre { white-space: pre-wrap; font-family: inherit; }
              </style>
            </head>
            <body>
              <pre>${content}</pre>
              <script>window.print();</script>
            </body>
          </html>
        `);
        printWindow.document.close();
      }
      return;
    }

    const mimeTypes = {
      txt: "text/plain",
      md: "text/markdown",
      docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    };
    const blob = new Blob([content], { type: mimeTypes[format as keyof typeof mimeTypes] || "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const lines = content ? content.split("\n").length : 0;

  return (
    <div className="flex h-full min-h-0 flex-col gap-2.5" data-testid="resume-document">
      {/* Header Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/40 pb-2">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <FileText size={15} />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-bold leading-tight text-foreground">Document Canvas</span>
              <Badge variant="outline" className="h-4 bg-emerald-500/10 text-[9px] font-semibold text-emerald-600 border-emerald-500/30">
                {fileFormat}
              </Badge>
            </div>
            <p className="text-[10px] text-muted-foreground">{lines} lines · Editable & Targetable</p>
          </div>
          {busy && (
            <Badge variant="secondary" className="animate-pulse text-[9px] font-mono">
              syncing…
            </Badge>
          )}
        </div>

        {/* Action Controls (View Mode, Undo/Redo, Edit, Export) */}
        <div className="flex items-center gap-1.5">
          <div className="flex items-center rounded-lg border border-border/60 bg-muted/40 p-0.5">
            <button
              type="button"
              onClick={() => setViewMode("preview")}
              className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium transition-colors ${
                viewMode === "preview" ? "bg-background text-foreground shadow-xs" : "text-muted-foreground hover:text-foreground"
              }`}
              title="Formatted Preview Mode"
            >
              <Eye size={11} />
              <span>Preview</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode("raw")}
              className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium transition-colors ${
                viewMode === "raw" ? "bg-background text-foreground shadow-xs" : "text-muted-foreground hover:text-foreground"
              }`}
              title="Raw Code Text Mode"
            >
              <FileCode size={11} />
              <span>Text</span>
            </button>
          </div>

          <Button variant="ghost" size="icon" className="h-7 w-7" title="Undo edit" disabled={!canUndo || busy} onClick={onUndo}>
            <Undo2 size={13} />
          </Button>
          <Button variant="ghost" size="icon" className="h-7 w-7" title="Redo edit" disabled={!canRedo || busy} onClick={onRedo}>
            <Redo2 size={13} />
          </Button>

          {editing ? (
            <div className="flex items-center gap-1">
              <Button variant="ghost" size="sm" className="h-7 px-2 text-xs" title="Cancel" onClick={cancelDraft}>
                <X size={13} />
              </Button>
              <Button size="sm" className="h-7 gap-1 px-3 text-xs bg-emerald-600 hover:bg-emerald-700 text-white" onClick={commitDraft} data-testid="save-resume">
                <Check size={13} /> Save
              </Button>
            </div>
          ) : (
            <Button
              variant="outline"
              size="sm"
              className="h-7 gap-1 px-2.5 text-xs"
              onClick={startEditing}
              data-testid="edit-resume"
              disabled={!content}
            >
              <Pencil size={12} /> Edit
            </Button>
          )}

          {/* Export Dropdown */}
          <Select onValueChange={(val) => handleExport(val as "txt" | "md" | "pdf" | "docx")}>
            <SelectTrigger className="h-7 gap-1 px-2 text-xs bg-primary text-primary-foreground font-semibold border-none hover:bg-primary/90">
              <Download size={12} />
              <span>Export</span>
            </SelectTrigger>
            <SelectContent align="end">
              <SelectItem value="pdf" className="text-xs font-medium cursor-pointer">
                <span className="flex items-center gap-2"><FileDown size={13} className="text-red-500" /> Export PDF (.pdf)</span>
              </SelectItem>
              <SelectItem value="docx" className="text-xs font-medium cursor-pointer">
                <span className="flex items-center gap-2"><FileType size={13} className="text-blue-500" /> Export Word (.docx)</span>
              </SelectItem>
              <SelectItem value="txt" className="text-xs font-medium cursor-pointer">
                <span className="flex items-center gap-2"><FileText size={13} className="text-slate-500" /> Export Text (.txt)</span>
              </SelectItem>
              <SelectItem value="md" className="text-xs font-medium cursor-pointer">
                <span className="flex items-center gap-2"><FileCode size={13} className="text-purple-500" /> Export Markdown (.md)</span>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Selection Banner */}
      {selection && !editing && (
        <div
          data-testid="selection-banner"
          className="flex items-start gap-2 rounded-xl border border-primary/30 bg-primary/5 px-3 py-2 text-xs text-foreground animate-in fade-in-50"
        >
          <TextSelect size={14} className="mt-0.5 shrink-0 text-primary" />
          <div className="min-w-0 flex-1">
            <span className="font-semibold">Lines {selection.startLine}–{selection.endLine} selected. </span>
            <span className="text-muted-foreground">
              Ask the assistant to rewrite exactly this section.
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

      {/* Document Body View (Formatted Paper Preview vs Raw Text Editor) */}
      {editing ? (
        <textarea
          ref={textareaRef}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          spellCheck={false}
          data-testid="resume-textarea"
          className="scrollbar-none min-h-0 w-full flex-1 resize-none rounded-xl border border-primary/40 bg-background p-4 font-mono text-xs leading-relaxed shadow-inner outline-none focus:ring-2 focus:ring-ring/40"
        />
      ) : (
        <div
          ref={displayRef}
          onMouseUp={captureSelection}
          onTouchEnd={captureSelection}
          data-testid="resume-content"
          className={cn(
            "scrollbar-none min-h-0 flex-1 cursor-text select-text overflow-y-auto rounded-xl border border-border/60 bg-white dark:bg-card p-5 text-xs leading-relaxed shadow-xs transition-all",
            !content && "flex items-center justify-center text-center text-muted-foreground"
          )}
        >
          {content ? (
            viewMode === "preview" ? (
              <div className="space-y-4 font-sans text-slate-800 dark:text-slate-100">
                {content.split("\n\n").map((paragraph, i) => {
                  const firstLine = paragraph.split("\n")[0];
                  const isHeading = firstLine && (firstLine === firstLine.toUpperCase() || firstLine.startsWith("#"));

                  return (
                    <div key={i} className="space-y-1">
                      {isHeading ? (
                        <h3 className="border-b border-slate-200 dark:border-slate-800 pb-1 font-bold uppercase tracking-wider text-primary text-xs">
                          {firstLine.replace(/^#+\s*/, "")}
                        </h3>
                      ) : (
                        <p className="whitespace-pre-wrap">{paragraph}</p>
                      )}
                      {isHeading && (
                        <p className="whitespace-pre-wrap pl-1">{paragraph.split("\n").slice(1).join("\n")}</p>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <pre className="font-mono text-xs whitespace-pre-wrap">{content}</pre>
            )
          ) : (
            <div className="space-y-2 text-center">
              <FileText size={24} className="mx-auto text-muted-foreground" />
              <p>Run a screening or paste text to view & edit your document here.</p>
            </div>
          )}
        </div>
      )}

      {!editing && content && !selection && (
        <p className="flex items-center gap-1.5 px-1 text-[10px] text-muted-foreground">
          <Sparkles size={11} className="text-primary" />
          Tip: Select any lines to target for AI rewrite, or click Edit to type directly.
        </p>
      )}
    </div>
  );
}

