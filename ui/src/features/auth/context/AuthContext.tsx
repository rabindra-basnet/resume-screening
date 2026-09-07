import {
  createContext,
  useContext,
  useEffect,
  type ReactNode,
} from "react";
import { useStore } from "@tanstack/react-store";
import type { User, AuthState } from "../store/authStore";
import { authStore, refreshUser, logoutUser } from "../store/authStore";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  loading: true,
  error: null,
  refresh: async () => {},
  logout: async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const { user, loading, error } = useStore<AuthState>(authStore);

  useEffect(() => {
    refreshUser();
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, loading, error, refresh: refreshUser, logout: logoutUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
