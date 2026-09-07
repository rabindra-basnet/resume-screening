import { useState } from "react";
import { apiPost, errMsg } from "@/shared/api/client";
import type { JobDescription } from "@/shared/types";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/shared/components/ui/card";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { Textarea } from "@/shared/components/ui/textarea";
import { Button } from "@/shared/components/ui/button";
import { Badge } from "@/shared/components/ui/badge";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { Plus, CheckCircle2, Copy, Sparkles } from "lucide-react";

const SAMPLE_JD = {
  title: "Senior Full Stack Engineer (Python & React)",
  rawText: `We are looking for a Senior Full Stack Engineer to lead the design and implementation of AI-driven web applications.

Key Responsibilities:
- Build resilient FastAPI backends with PostgreSQL and SQLAlchemy.
- Create responsive client interfaces using React, TypeScript, and Tailwind CSS.
- Optimize LLM prompt chains and integrate agentic workflows.
- Design RESTful APIs and handle automated testing with Pytest.

Requirements:
- 4+ years of professional software engineering experience.
- Deep expertise in Python, React, TypeScript, and Docker.
- Experience with PostgreSQL, Redis, and cloud deployments (AWS/Vercel).
- Strong background in system architecture and AI model integration.`,
};

export function CreateJobForm() {
  const [title, setTitle] = useState("");
  const [rawText, setRawText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [createdJD, setCreatedJD] = useState<JobDescription | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState(false);

  const handleFillSample = () => {
    setTitle(SAMPLE_JD.title);
    setRawText(SAMPLE_JD.rawText);
  };

  const createJD = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setCreateError(null);
    setCreatedJD(null);
    try {
      const data = await apiPost<JobDescription>("/job-descriptions", {
        title,
        raw_text: rawText,
      });
      setCreatedJD(data);
      setTitle("");
      setRawText("");
    } catch (e) {
      setCreateError(errMsg(e));
    } finally {
      setSubmitting(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  };

  return (
    <Card className="border-border/60 bg-card/80 backdrop-blur shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <div>
          <CardTitle className="text-xl">Create New Job Description</CardTitle>
          <CardDescription>
            Paste job posting details below. The parser will extract key skills and experience requirements.
          </CardDescription>
        </div>
        <Button
          variant="outline"
          size="sm"
          type="button"
          onClick={handleFillSample}
          className="gap-1.5 text-xs"
        >
          <Sparkles size={14} className="text-primary" /> Load Sample Template
        </Button>
      </CardHeader>
      <CardContent>
        <form onSubmit={createJD} className="space-y-5">
          <div>
            <Label htmlFor="title" className="text-sm font-medium">Job Title</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              placeholder="e.g. Senior Software Engineer"
              className="mt-1.5 bg-background/50"
            />
          </div>
          <div>
            <Label htmlFor="raw_text" className="text-sm font-medium">Job Description Text</Label>
            <Textarea
              id="raw_text"
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              required
              placeholder="Paste the full job description text here..."
              className="mt-1.5 min-h-[180px] bg-background/50 leading-relaxed"
            />
          </div>
          <Button type="submit" disabled={submitting} className="gap-2">
            {submitting ? (
              <>
                <Skeleton className="h-4 w-4 rounded-full" />
                Parsing & Extracting Skills...
              </>
            ) : (
              <>
                <Plus size={16} /> Create Job Description
              </>
            )}
          </Button>
        </form>

        {createError && (
          <div className="mt-4 p-4 rounded-xl bg-destructive/10 border border-destructive/30 text-sm text-destructive">
            {createError}
          </div>
        )}

        {createdJD && (
          <Card className="mt-6 border-emerald-500/30 bg-emerald-500/5 dark:bg-emerald-500/10">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-semibold text-sm">
                  <CheckCircle2 size={18} /> Job Description Created Successfully!
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => createdJD.id && copyToClipboard(createdJD.id)}
                  className="gap-1.5 text-xs"
                >
                  <Copy size={12} /> {copiedId ? "Copied ID!" : "Copy JD ID"}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">JD ID:</span>
                <code className="rounded-md bg-muted px-2 py-0.5 font-mono text-xs font-semibold">
                  {createdJD.id}
                </code>
              </div>
              <div>
                <span className="font-semibold block mb-1.5">Extracted Skills ({createdJD.skills?.length || 0}):</span>
                <div className="flex flex-wrap gap-1.5">
                  {(createdJD.skills || []).map((skill) => (
                    <Badge key={skill} variant="secondary" className="px-2.5 py-1 text-xs">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </CardContent>
    </Card>
  );
}
