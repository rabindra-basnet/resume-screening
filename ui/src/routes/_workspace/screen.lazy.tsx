import { createLazyFileRoute } from "@tanstack/react-router";
import { ScreenPage } from "@/features/screening";

export const Route = createLazyFileRoute("/_workspace/screen")({
  component: ScreenPage,
});
