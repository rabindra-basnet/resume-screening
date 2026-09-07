import { useRef } from "react";
import { UploadCloud, FileCheck } from "lucide-react";
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
      <Label className="text-sm font-semibold mb-2 block">Resume Document (PDF or DOCX)</Label>
      <div
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`relative cursor-pointer rounded-2xl border-2 border-dashed p-8 text-center transition-all ${
          dragging
            ? "border-primary bg-primary/10 scale-[0.99]"
            : selectedFile
            ? "border-emerald-500/50 bg-emerald-500/5"
            : "border-border/80 bg-muted/40 hover:bg-muted/70 hover:border-primary/50"
        }`}
      >
        {selectedFile ? (
          <div className="flex flex-col items-center justify-center space-y-2">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <FileCheck size={28} />
            </div>
            <p className="text-base font-semibold text-foreground">{selectedFile.name}</p>
            <p className="text-xs text-muted-foreground">
              {(selectedFile.size / 1024).toFixed(1)} KB • Click to change file
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center space-y-2">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <UploadCloud size={28} />
            </div>
            <p className="text-base font-semibold text-foreground">
              Drop resume here, or <span className="text-primary underline">browse</span>
            </p>
            <p className="text-xs text-muted-foreground">Supports PDF and DOCX files</p>
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
