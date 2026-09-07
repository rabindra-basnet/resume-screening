import { Briefcase, GraduationCap, Sparkles, Upload } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/components/ui/tabs";
import { CvBuilder } from "../components/CvBuilder";
import { CreateJobForm } from "@/features/jobs/components/CreateJobForm";
import { JobLookupView } from "@/features/jobs/components/JobLookupView";
import LearningPage from "@/features/learning/page/LearningPage";

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

      {/* Single Screen Tabs Container */}
      <Tabs defaultValue="screen" className="w-full space-y-6">
        <div className="flex items-center justify-between border-b border-border/60">
          <TabsList className="h-auto gap-1 bg-transparent p-0">
            <TabsTrigger
              value="screen"
              className="gap-2 rounded-t-lg border-b-2 border-transparent px-4 py-2.5 font-semibold text-sm transition-all data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:text-primary"
            >
              <Upload size={16} /> Screen Resume
            </TabsTrigger>
            <TabsTrigger
              value="jobs"
              className="gap-2 rounded-t-lg border-b-2 border-transparent px-4 py-2.5 font-semibold text-sm transition-all data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:text-primary"
            >
              <Briefcase size={16} /> Job Descriptions
            </TabsTrigger>
            <TabsTrigger
              value="learning"
              className="gap-2 rounded-t-lg border-b-2 border-transparent px-4 py-2.5 font-semibold text-sm transition-all data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:text-primary"
            >
              <GraduationCap size={16} /> Learning Roadmap
            </TabsTrigger>
          </TabsList>
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
