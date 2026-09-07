import { Link } from "@tanstack/react-router";
import { Plus, Search, Upload, Briefcase, GraduationCap, Sparkles } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/components/ui/tabs";
import { CreateJobForm } from "../components/CreateJobForm";
import { JobLookupView } from "../components/JobLookupView";

export default function JobsPage() {
  return (
    <div className="space-y-8 fade-in">
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
          <Sparkles size={13} /> Agentic Talent Workspace
        </div>
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
          Job Descriptions
        </h1>
        <p className="max-w-2xl text-muted-foreground">
          Create, parse, and reference job requirements. Structured skill requirements are automatically extracted for resume screening.
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

      <Tabs defaultValue="create" className="w-full">
        <TabsList className="grid w-full grid-cols-2 max-w-md mb-6">
          <TabsTrigger value="create" className="gap-2">
            <Plus size={16} /> Create Job Description
          </TabsTrigger>
          <TabsTrigger value="lookup" className="gap-2">
            <Search size={16} /> Lookup by ID
          </TabsTrigger>
        </TabsList>

        <TabsContent value="create">
          <CreateJobForm />
        </TabsContent>

        <TabsContent value="lookup">
          <JobLookupView />
        </TabsContent>
      </Tabs>
    </div>
  );
}
