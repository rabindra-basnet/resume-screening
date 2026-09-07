import { createLazyFileRoute } from "@tanstack/react-router";
import { AccountPage } from "@/features/account";

export const Route = createLazyFileRoute("/_workspace/account")({
  component: AccountPage,
});
