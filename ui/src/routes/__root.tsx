import React, { Suspense } from "react";
import { createRootRoute } from "@tanstack/react-router";
import { AuthProvider } from "@/features/auth/context/AuthContext";
import Layout from "@/shared/components/Layout";

const TanStackRouterDevtools = import.meta.env.PROD
  ? () => null
  : React.lazy(() =>
      import("@tanstack/router-devtools").then((res) => ({
        default: res.TanStackRouterDevtools,
      }))
    );

export const Route = createRootRoute({
  component: RootComponent,
});

function RootComponent() {
  return (
    <AuthProvider>
      <Layout />
      <Suspense fallback={null}>
        <TanStackRouterDevtools position="bottom-right" />
      </Suspense>
    </AuthProvider>
  );
}
