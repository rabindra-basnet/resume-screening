import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { FileText, Briefcase, Upload, GraduationCap, LogIn } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

const navItems = [
  { to: "/screen", label: "Screen Resume", icon: Upload },
  { to: "/jobs", label: "Job Descriptions", icon: Briefcase },
  { to: "/learning", label: "Learning Center", icon: GraduationCap },
];

export default function Layout({ children }: { children: ReactNode }) {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-app-bg text-text">
      <header
        className="sticky top-0 z-30 bg-app-surface border-b"
        style={{ borderColor: "var(--color-border)" }}
      >
        <div
          className="flex items-center justify-between gap-6 h-16 max-w-6xl mx-auto px-6"
          style={{ borderColor: "var(--color-border)" }}
        >
          <NavLink to="/" className="flex items-center gap-2.5 no-underline">
            <span
              className="w-9 h-9 rounded-lg flex items-center justify-center"
              style={{ background: "var(--color-brand-soft)" }}
            >
              <FileText size={20} style={{ color: "var(--color-brand)" }} />
            </span>
            <span className="font-semibold text-base" style={{ color: "var(--color-text)" }}>
              AetherGate
              <span className="font-normal ml-1.5 text-sm" style={{ color: "var(--color-text-muted)" }}>
                Resume Screening
              </span>
            </span>
          </NavLink>

          <nav className="flex items-center gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium no-underline transition-colors ${
                    isActive ? "font-semibold" : ""
                  }`
                }
                style={({ isActive }) => ({
                  color: isActive ? "var(--color-brand)" : "var(--color-text-muted)",
                  background: isActive ? "var(--color-brand-soft)" : "transparent",
                })}
              >
                <item.icon size={17} />
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            {user ? (
              <>
                <NavLink
                  to="/account"
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm no-underline transition-colors ${
                      isActive ? "font-semibold" : ""
                    }`
                  }
                  style={({ isActive }) => ({
                    color: isActive ? "var(--color-brand)" : "var(--color-text-muted)",
                    background: isActive ? "var(--color-brand-soft)" : "transparent",
                  })}
                >
                  {user.avatar_url ? (
                    <img
                      src={user.avatar_url}
                      alt=""
                      className="w-6 h-6 rounded-full"
                    />
                  ) : null}
                  {user.name}
                </NavLink>
                <a
                  href="/api/v1/auth/logout"
                  className="text-xs no-underline transition-colors hover:opacity-80"
                  style={{ color: "var(--color-text-muted)" }}
                >
                  Sign out
                </a>
              </>
            ) : (
              <NavLink
                to="/login"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium no-underline transition-colors"
                style={{
                  color: "var(--color-text-muted)",
                }}
              >
                <LogIn size={15} />
                Sign in
              </NavLink>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">{children}</main>

      <footer
        className="border-t py-6 mt-8"
        style={{ borderColor: "var(--color-border)", color: "var(--color-text-muted)" }}
      >
        <div className="max-w-6xl mx-auto px-6 text-sm">
          AetherGate — AI-powered resume screening &amp; candidate matching
        </div>
      </footer>
    </div>
  );
}
