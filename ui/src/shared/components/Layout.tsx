import { Link, Outlet } from "@tanstack/react-router";
import { FileText, Sparkles, LogIn, LogOut } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import {
  Avatar,
  AvatarImage,
  AvatarFallback,
} from "@/shared/components/ui/avatar";
import { Button } from "@/shared/components/ui/button";

export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground selection:bg-primary selection:text-primary-foreground font-sans">
      {/* Header Navigation */}
      <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur-md supports-[backdrop-filter]:bg-background/60">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6">
          {/* Brand Logo */}
          <Link to="/" className="flex items-center gap-3 no-underline group">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm transition-transform group-hover:scale-105">
              <FileText size={20} />
            </div>
            <div className="flex flex-col">
              <span className="text-base font-bold tracking-tight leading-tight">
                TalentPulse AI
              </span>
              <span className="text-[11px] font-medium text-muted-foreground">
                Resume Screening AI
              </span>
            </div>
          </Link>

          {/* Workspace Action */}
          <div className="flex items-center gap-3">
            <Link to="/screen">
              <Button
                size="sm"
                variant="default"
                className="gap-2 rounded-xl font-semibold shadow-xs"
              >
                <Sparkles size={15} />
                Agentic Workspace
              </Button>
            </Link>

            {user ? (
              <div className="flex items-center gap-2">
                <Link
                  to="/account"
                  activeProps={{
                    className: "ring-2 ring-primary/40 bg-muted",
                  }}
                  className="flex items-center gap-2.5 rounded-xl px-3 py-1.5 text-sm text-foreground no-underline transition-all hover:bg-muted border border-border/60"
                >
                  <Avatar className="h-7 w-7">
                    {user.avatar_url ? (
                      <AvatarImage src={user.avatar_url} alt={user.name} />
                    ) : null}
                    <AvatarFallback className="bg-primary/10 text-primary font-bold text-xs">
                      {user.name?.charAt(0)?.toUpperCase() || "U"}
                    </AvatarFallback>
                  </Avatar>
                  <span className="font-semibold text-xs hidden sm:inline">
                    {user.name}
                  </span>
                </Link>

                <button
                  type="button"
                  onClick={() => logout()}
                  className="flex items-center gap-1 rounded-xl px-2.5 py-1.5 text-xs font-medium text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors border-0 bg-transparent cursor-pointer"
                  title="Sign out"
                >
                  <LogOut size={14} />
                  <span className="hidden sm:inline">Logout</span>
                </button>
              </div>
            ) : (
              <Link to="/login">
                <Button
                  size="sm"
                  variant="outline"
                  className="gap-2 rounded-xl font-semibold"
                >
                  <LogIn size={15} />
                  Sign In
                </Button>
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 sm:px-6 py-8">
        <Outlet />
      </main>

      {/* Clean Minimal Footer */}
      <footer className="border-t border-border/40 py-6 bg-card/20 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 sm:px-6 text-xs text-muted-foreground">
          <span>© TalentPulse AI</span>
        </div>
      </footer>
    </div>
  );
}
