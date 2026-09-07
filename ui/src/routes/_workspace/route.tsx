import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { refreshUser, authStore } from "@/features/auth";

export const Route = createFileRoute("/_workspace")({
  beforeLoad: () => {
    // Check cached auth state synchronously so navigation is instant
    const { user, loading } = authStore.state;
    // Trigger background revalidation non-blockingly if not loading
    if (!loading) {
      refreshUser().catch(() => {});
    }
    if (!loading && !user) {
      throw redirect({ to: "/login" });
    }
  },
  component: WorkspaceLayout,
});

function WorkspaceLayout() {
  return <Outlet />;
}
