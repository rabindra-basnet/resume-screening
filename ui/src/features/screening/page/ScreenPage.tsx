import { Link } from "@tanstack/react-router";
import { Briefcase, GraduationCap, Sparkles, Upload } from "lucide-react";
import { CvBuilder } from "../components/CvBuilder";

export default function ScreenPage() {
  return (
    <div className="space-y-8 fade-in">
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
          <Sparkles size={13} /> Agentic Talent Workspace
        </div>
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
          Get your resume ready in three steps
        </h1>
        <p className="max-w-2xl text-muted-foreground">
          Upload a resume, let the AI agents make it ATS- and hiring-tool-friendly, iterate via
          chat, then learn the skills you're missing before you apply.
        </p>
      </div>

      {/* Single Workspace Navigation Tabs */}
      <div className="flex items-center justify-between border-b border-border/60">
        <div className="flex items-center gap-1">
          <Link
            to="/screen"
            activeProps={{
              className: "border-primary text-primary font-bold",
            }}
            inactiveProps={{
              className: "border-transparent text-muted-foreground hover:text-foreground",
            }}
            className="flex items-center gap-2 rounded-t-lg border-b-2 px-4 py-2.5 font-semibold text-sm transition-all"
          >
            <Upload size={16} /> Screen Resume
          </Link>
          <Link
            to="/jobs"
            activeProps={{
              className: "border-primary text-primary font-bold",
            }}
            inactiveProps={{
              className: "border-transparent text-muted-foreground hover:text-foreground",
            }}
            className="flex items-center gap-2 rounded-t-lg border-b-2 px-4 py-2.5 font-semibold text-sm transition-all"
          >
            <Briefcase size={16} /> Job Descriptions
          </Link>
          <Link
            to="/learning"
            activeProps={{
              className: "border-primary text-primary font-bold",
            }}
            inactiveProps={{
              className: "border-transparent text-muted-foreground hover:text-foreground",
            }}
            className="flex items-center gap-2 rounded-t-lg border-b-2 px-4 py-2.5 font-semibold text-sm transition-all"
          >
            <GraduationCap size={16} /> Learning Roadmap
          </Link>
        </div>
      </div>

      {/* Screen Resume Workspace */}
      <CvBuilder />
    </div>
  );
}
