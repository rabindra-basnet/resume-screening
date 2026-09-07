import { useRef } from "react";
import { UploadCloud, FileCheck, FileText } from "lucide-react";
import { Label } from "@/shared/components/ui/label";

interface ResumeDropzoneProps {
  selectedFile: File | null;
  dragging: boolean;
  setDragging: (dragging: boolean) => void;
  onSelectFile: (file: File) => void;
}

export function ResumeDropzone({
  selectedFile,
  dragging,
  setDragging,
  onSelectFile,
}: ResumeDropzoneProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files.length) onSelectFile(e.dataTransfer.files[0]);
  };

  return (
    <div>
      <Label className="text-sm font-semibold mb-3 block">Resume Document (PDF or DOCX)</Label>
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload resume file"
        onClick={() => fileInputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            fileInputRef.current?.click();
          }
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`relative flex min-h-[280px] cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 text-center transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
          dragging
            ? "border-primary bg-primary/10 scale-[0.99]"
            : selectedFile
            ? "border-emerald-500/50 bg-emerald-500/5"
            : "border-border/80 bg-muted/40 hover:bg-muted/70 hover:border-primary/50"
        }`}
      >
        {selectedFile ? (
          <div className="flex flex-col items-center justify-center space-y-3">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <FileCheck size={36} />
            </div>
            <p className="text-lg font-semibold text-foreground">{selectedFile.name}</p>
            <p className="text-sm text-muted-foreground">
              {(selectedFile.size / 1024).toFixed(1)} KB • Click to change file
            </p>
            <div className="flex items-center gap-1.5 rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
              <FileText size={13} /> Ready for screening
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-primary/10 text-primary">
              <UploadCloud size={44} />
            </div>
            <p className="text-2xl font-bold text-foreground">Drop your resume here</p>
            <p className="text-base text-muted-foreground">
              or <span className="font-semibold text-primary underline underline-offset-4">browse</span>
            </p>
            <p className="text-sm text-muted-foreground">Supports PDF and DOCX files</p>
          </div>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx"
          hidden
          onChange={(e) => {
            if (e.target.files?.length) onSelectFile(e.target.files[0]);
          }}
        />
      </div>
    </div>
  );
}
