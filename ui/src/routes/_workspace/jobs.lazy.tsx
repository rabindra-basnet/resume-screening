import { createLazyFileRoute } from "@tanstack/react-router";
import { JobsPage } from "@/features/jobs";

export const Route = createLazyFileRoute("/_workspace/jobs")({
  component: JobsPage,
});
