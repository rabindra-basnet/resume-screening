import { createLazyFileRoute } from "@tanstack/react-router";
import { LearningPage } from "@/features/learning";

export const Route = createLazyFileRoute("/_workspace/learning")({
  component: LearningPage,
});
