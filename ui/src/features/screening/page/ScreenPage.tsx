import { Briefcase, GraduationCap, Sparkles, Upload } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/components/ui/tabs";
import { CvBuilder } from "../components/CvBuilder";
import { CreateJobForm } from "@/features/jobs/components/CreateJobForm";
import { JobLookupView } from "@/features/jobs/components/JobLookupView";
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
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
                <Sparkles size={13} /> Agentic Talent Workspace
              </div>
              <h1 className="text-3xl font-bold tracking-tight sm:text-4xl leading-tight">
                Get your resume ready in three steps
              </h1>
              <p className="max-w-2xl text-muted-foreground leading-relaxed">
                Upload a resume, let the AI agents make it ATS- and hiring-tool-friendly,
                iterate via chat, then learn the skills you're missing before you apply.
              </p>
            </div>

            {/* Workflow summary card */}
            <div className="hidden lg:flex flex-col justify-center gap-1.5 rounded-2xl border border-border/60 bg-card/50 p-5 backdrop-blur">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                How it works
              </p>
              {[
                { n: "1", t: "Review", d: "Upload & multi-agent screening" },
                { n: "2", t: "Iterate", d: "Chat + refined agent edits" },
                { n: "3", t: "Apply", d: "Submit the polished resume" },
              ].map((s) => (
                <div key={s.n} className="flex items-center gap-3">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
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
          <div className="border-b border-border/60">
            <TabsList className="h-auto gap-1 bg-transparent p-0">
              <TabsTrigger
                value="screen"
                className="gap-2 rounded-none border-b-2 border-transparent px-5 py-3 font-semibold text-sm transition-all data-[state=active]:border-primary data-[state=active]:text-primary data-[state=active]:shadow-none hover:bg-muted/40"
              >
                <Upload size={16} /> Screen Resume
              </TabsTrigger>
              <TabsTrigger
                value="jobs"
                className="gap-2 rounded-none border-b-2 border-transparent px-5 py-3 font-semibold text-sm transition-all data-[state=active]:border-primary data-[state=active]:text-primary data-[state=active]:shadow-none hover:bg-muted/40"
              >
                <Briefcase size={16} /> Job Descriptions
              </TabsTrigger>
              <TabsTrigger
                value="learning"
                className="gap-2 rounded-none border-b-2 border-transparent px-5 py-3 font-semibold text-sm transition-all data-[state=active]:border-primary data-[state=active]:text-primary data-[state=active]:shadow-none hover:bg-muted/40"
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

        {/* Tab 2: Job Descriptions Workspace */}
        <TabsContent value="jobs" className="space-y-6 focus-visible:outline-none">
          <div className="space-y-1">
            <h2 className="text-2xl font-bold tracking-tight">Job Descriptions</h2>
            <p className="text-muted-foreground">
              Create, parse, and reference job requirements for resume screening.
            </p>
          </div>
          <Tabs defaultValue="create" className="w-full">
            <TabsList className="grid w-full grid-cols-2 max-w-md mb-6">
              <TabsTrigger value="create">Create Job Description</TabsTrigger>
              <TabsTrigger value="lookup">Lookup by ID</TabsTrigger>
            </TabsList>
            <TabsContent value="create">
              <CreateJobForm />
            </TabsContent>
            <TabsContent value="lookup">
              <JobLookupView />
            </TabsContent>
          </Tabs>
        </TabsContent>

        {/* Tab 3: Learning Roadmap Workspace */}
        <TabsContent value="learning" className="space-y-6 focus-visible:outline-none">
          <LearningPage />
        </TabsContent>
      </Tabs>
    </div>
  );
}
