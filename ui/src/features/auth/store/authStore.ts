import { createStore } from "@tanstack/react-store";
import { apiGet, apiPost } from "@/shared/api/client";

export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
}

export interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

export const authStore = createStore<AuthState>({
  user: null,
  loading: true,
  error: null,
});

export function setUser(user: User | null) {
  authStore.setState((s) => ({ ...s, user }));
}
export function setLoading(loading: boolean) {
  authStore.setState((s) => ({ ...s, loading }));
}
export function setError(error: string | null) {
  authStore.setState((s) => ({ ...s, error }));
}

export async function refreshUser(): Promise<void> {
  if (refreshPromise) {
    return refreshPromise;
  }
  refreshPromise = doRefresh();
  try {
    await refreshPromise;
  } finally {
    refreshPromise = null;
  }
}

let refreshPromise: Promise<void> | null = null;

async function doRefresh(): Promise<void> {
  setLoading(true);
  setError(null);
  try {
    const me = await apiGet<User>("/auth/me");
    setUser(me);
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    setUser(null);
    setError(msg);
  } finally {
    setLoading(false);
  }
}

export async function logoutUser(): Promise<void> {
  try {
    await apiPost("/auth/logout", {});
  } catch {
    // Ignore logout errors
  } finally {
    setUser(null);
  }
}
