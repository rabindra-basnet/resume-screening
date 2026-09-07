import { createRootRoute } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/router-devtools";
import { AuthProvider } from "@/contexts/AuthContext";
import Layout from "@/shared/components/Layout";

export const Route = createRootRoute({
  component: RootComponent,
});

function RootComponent() {
  return (
    <AuthProvider>
      <Layout />
      <TanStackRouterDevtools position="bottom-right" />
    </AuthProvider>
  );
}
