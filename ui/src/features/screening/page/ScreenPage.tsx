import { Briefcase, GraduationCap, Sparkles, Upload } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/components/ui/tabs";
import { CvBuilder } from "../components/CvBuilder";
import { CreateJobForm } from "@/features/jobs/components/CreateJobForm";
import { JobLookupView } from "@/features/jobs/components/JobLookupView";
import { LearningPage } from "@/features/learning";

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

      {/* Single Workspace Tabs */}
      <Tabs defaultValue="screen" className="w-full space-y-6">
        <div className="flex items-center justify-between border-b border-border/60">
          <TabsList className="h-auto gap-1 bg-transparent p-0">
            <TabsTrigger
              value="screen"
              className="gap-2 rounded-t-lg border-b-2 border-transparent px-4 py-2.5 font-semibold data-[state=active]:border-primary data-[state=active]:bg-transparent"
            >
              <Upload size={16} /> Screen Resume
            </TabsTrigger>
            <TabsTrigger
              value="jobs"
              className="gap-2 rounded-t-lg border-b-2 border-transparent px-4 py-2.5 font-semibold data-[state=active]:border-primary data-[state=active]:bg-transparent"
            >
              <Briefcase size={16} /> Job Descriptions
            </TabsTrigger>
            <TabsTrigger
              value="learning"
              className="gap-2 rounded-t-lg border-b-2 border-transparent px-4 py-2.5 font-semibold data-[state=active]:border-primary data-[state=active]:bg-transparent"
            >
              <GraduationCap size={16} /> Learning Roadmap
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Tab 1: Screen Resume */}
        <TabsContent value="screen" className="space-y-8">
          <CvBuilder />
        </TabsContent>

        {/* Tab 2: Job Descriptions */}
        <TabsContent value="jobs" className="space-y-6">
          <div className="space-y-1">
            <h2 className="text-2xl font-bold tracking-tight">Job Descriptions</h2>
            <p className="text-muted-foreground">
              Save job descriptions to reuse during screening and CV matching.
            </p>
          </div>
          <CreateJobForm />
          <JobLookupView />
        </TabsContent>

        {/* Tab 3: Learning Roadmap */}
        <TabsContent value="learning" className="space-y-6">
          <LearningPage />
        </TabsContent>
      </Tabs>
    </div>
  );
}
