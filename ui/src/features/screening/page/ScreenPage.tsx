import { GraduationCap, Sparkles, Upload } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/components/ui/tabs";
import { CvBuilder } from "../components/CvBuilder";
import LearningPage from "@/features/learning/page/LearningPage";

export default function ScreenPage() {
  return (
    <div className="w-full space-y-8 fade-in">
      {/* Workspace Tabs Container */}
      <Tabs defaultValue="screen" className="w-full space-y-8">
        {/* Page Header + Tabs bar */}
        <div className="space-y-8">
          {/* Page Header: heading left, workflow hint right */}
          <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(380px,0.8fr)]">
            <div className="space-y-3">
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3.5 py-1 text-xs font-semibold text-primary shadow-xs">
                <Sparkles size={13} /> Agentic Talent Workspace
              </div>
              <h1 className="text-3xl font-bold tracking-tight sm:text-4xl leading-tight">
                Get your resume ready in three steps
              </h1>
              <p className="max-w-2xl text-muted-foreground leading-relaxed text-sm sm:text-base">
                Upload a resume, paste your target job description, let AI agents optimize ATS fit &amp; tone,
                iterate via chat, then discover missing skill learning roadmaps.
              </p>
            </div>

            {/* Workflow summary card */}
            <div className="hidden lg:flex flex-col justify-center gap-2 rounded-2xl border border-border/80 bg-card/60 p-5 shadow-sm backdrop-blur">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">
                How it works
              </p>
              {[
                { n: "1", t: "Review", d: "Upload resume & paste job details" },
                { n: "2", t: "Iterate", d: "Chat + refined AI agent edits" },
                { n: "3", t: "Apply", d: "Submit the polished resume" },
              ].map((s) => (
                <div key={s.n} className="flex items-center gap-3">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary border border-primary/20">
                    {s.n}
                  </span>
                  <div className="flex items-baseline gap-2 min-w-0">
                    <span className="text-sm font-semibold text-foreground">{s.t}</span>
                    <span className="truncate text-xs text-muted-foreground">{s.d}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Full-width tabs */}
          <div className="border-b border-border/70">
            <TabsList className="h-auto gap-2 bg-transparent p-0">
              <TabsTrigger
                value="screen"
                className="gap-2 rounded-t-xl border-b-2 border-transparent px-6 py-3 font-semibold text-sm transition-all data-[state=active]:border-primary data-[state=active]:bg-card/70 data-[state=active]:text-primary data-[state=active]:shadow-xs hover:bg-muted/50"
              >
                <Upload size={16} /> Screen Resume
              </TabsTrigger>
              <TabsTrigger
                value="learning"
                className="gap-2 rounded-t-xl border-b-2 border-transparent px-6 py-3 font-semibold text-sm transition-all data-[state=active]:border-primary data-[state=active]:bg-card/70 data-[state=active]:text-primary data-[state=active]:shadow-xs hover:bg-muted/50"
              >
                <GraduationCap size={16} /> Learning Roadmap
              </TabsTrigger>
            </TabsList>
          </div>
        </div>

        {/* Tab 1: Screen Resume Workspace */}
        <TabsContent value="screen" className="space-y-6 focus-visible:outline-none">
          <CvBuilder />
        </TabsContent>

        {/* Tab 2: Learning Roadmap Workspace */}
        <TabsContent value="learning" className="space-y-6 focus-visible:outline-none">
          <LearningPage />
        </TabsContent>
      </Tabs>
    </div>
  );
}
