import { createLazyFileRoute } from "@tanstack/react-router";
import { ScreenPage } from "@/features/screening";

export const Route = createLazyFileRoute("/screen/$sessionId")({
  component: ScreenPage,
});
