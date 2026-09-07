import { createFileRoute } from "@tanstack/react-router";

export interface LearningSearch {
  q?: string;
}

export const Route = createFileRoute("/_workspace/learning")({
  validateSearch: (search: Record<string, unknown>): LearningSearch => ({
    q: typeof search.q === "string" ? search.q : undefined,
  }),
});


