import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { apiGet } from "../lib/api";

export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
}

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  loading: true,
  error: null,
  refresh: async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    try {
      setLoading(true);
      setError(null);
      const me = await apiGet<User>("/auth/me");
      setUser(me);
    } catch (err: unknown) {
      // 401 is expected when not logged in — don't treat as error.
      const msg = err instanceof Error ? err.message : String(err);
      if (msg.includes("401") || msg.includes("Not authenticated")) {
        setUser(null);
      } else {
        setUser(null);
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, error, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
