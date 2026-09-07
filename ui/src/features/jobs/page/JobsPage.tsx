import { Plus, Search } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/components/ui/tabs";
import { CreateJobForm } from "../components/CreateJobForm";
import { JobLookupView } from "../components/JobLookupView";

export default function JobsPage() {
  return (
    <div className="space-y-8 fade-in">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Job Descriptions</h1>
        <p className="text-muted-foreground mt-1 max-w-2xl">
          Create, parse, and reference job requirements. Structured skill requirements are automatically extracted for resume screening.
        </p>
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
