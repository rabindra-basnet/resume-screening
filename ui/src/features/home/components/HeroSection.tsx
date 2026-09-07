import { Link } from "@tanstack/react-router";
import { Sparkles, ArrowRight, ShieldCheck, CheckCircle, Bot } from "lucide-react";
import { useAuth } from "@/features/auth";
import { Button } from "@/shared/components/ui/button";
import { Badge } from "@/shared/components/ui/badge";

export function HeroSection() {
  const { user } = useAuth();

  return (
    <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 border border-slate-800 p-8 md:p-14 text-white shadow-xl">
      {/* Background ambient lighting */}
      <div className="absolute top-0 right-0 -mt-16 -mr-16 h-80 w-80 rounded-full bg-blue-500/20 blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-1/3 -mb-16 h-64 w-64 rounded-full bg-indigo-500/15 blur-3xl pointer-events-none" />

      <div className="relative max-w-3xl space-y-6">
        <Badge variant="outline" className="gap-1.5 px-3 py-1 text-xs font-semibold border-blue-400/40 text-blue-300 bg-blue-500/10 backdrop-blur">
          <Bot size={14} className="text-blue-400" /> Multi-Agent Job & Resume Matching Engine
        </Badge>

        <h1 className="text-4xl font-extrabold tracking-tight md:text-6xl leading-[1.15] bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent">
          Precision Resume Screening & Job Requirement Alignment
        </h1>

        <p className="text-lg md:text-xl text-slate-300 leading-relaxed max-w-2xl font-normal">
          Empowering job seekers and hiring teams with autonomous AI agents. Match candidate resumes directly against official company Job Descriptions (JDs), pinpoint skill gaps, and get instant recommendations.
        </p>

        <div className="flex flex-wrap items-center gap-4 pt-2">
          {user ? (
            <Link to="/screen">
              <Button size="lg" className="gap-2 font-semibold shadow-lg bg-blue-600 hover:bg-blue-500 text-white rounded-xl px-6">
                Open Workspace & Match Resume
                <ArrowRight size={18} />
              </Button>
            </Link>
          ) : (
            <Link to="/login">
              <Button size="lg" className="gap-2 font-semibold shadow-lg bg-blue-600 hover:bg-blue-500 text-white rounded-xl px-6">
                Get Started Free
                <ArrowRight size={18} />
              </Button>
            </Link>
          )}

          <Link to="/screen">
            <Button variant="outline" size="lg" className="gap-2 rounded-xl border-slate-700 bg-slate-800/60 hover:bg-slate-800 text-slate-200">
              <Sparkles size={16} className="text-amber-400" /> Interactive Agent Pipeline
            </Button>
          </Link>
        </div>

        <div className="flex flex-wrap items-center gap-6 pt-4 text-xs text-slate-400 font-medium border-t border-slate-800/80">
          <span className="flex items-center gap-1.5">
            <ShieldCheck size={16} className="text-emerald-400" /> Enterprise Privacy Protected
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle size={16} className="text-blue-400" /> Contextual JD vs CV Skill Analysis
          </span>
        </div>
      </div>
    </section>
  );
}
