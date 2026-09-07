import { createFileRoute } from "@tanstack/react-router";
import { apiGet } from "@/shared/api/client";
import type { AccountDocument } from "@/features/account";

export const Route = createFileRoute("/_workspace/account")({
  loader: async () => {
    try {
      return await apiGet<AccountDocument[]>("/account/documents");
    } catch {
      return [];
    }
  },
});


