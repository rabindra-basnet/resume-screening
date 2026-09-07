import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { refreshUser, authStore } from "@/features/auth";

export const Route = createFileRoute("/_workspace")({
  beforeLoad: async () => {
    await refreshUser();
    const { user } = authStore.state;
    if (!user) {
      throw redirect({ to: "/login" });
    }
  },
  component: WorkspaceLayout,
});

function WorkspaceLayout() {
  return <Outlet />;
}
