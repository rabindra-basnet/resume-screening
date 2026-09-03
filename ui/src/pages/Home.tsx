import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet, errMsg } from "../lib/api";
import type { HealthResponse } from "../lib/types";
import {
  Briefcase,
  Upload,
  GraduationCap,
  ShieldCheck,
  Cpu,
  FileSearch,
  Sparkles,
  ArrowRight,
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

const features = [
  {
    to: "/screen",
    title: "Screen Resume",
    desc: "Upload a resume and get an AI evaluation against a job description.",
    icon: Upload,
  },
  {
    to: "/jobs",
    title: "Job Descriptions",
    desc: "Create, store, and manage job descriptions for reuse.",
    icon: Briefcase,
  },
  {
    to: "/learning",
    title: "Learning Center",
    desc: "Get personalized resources to close your skill gaps.",
    icon: GraduationCap,
  },
];

const highlights = [
  {
    icon: FileSearch,
    title: "Smart Parsing",
    desc: "Automatically extracts candidate profile, skills, and experience from PDF or DOCX resumes.",
  },
  {
    icon: Cpu,
    title: "Multi-Model AI",
    desc: "Powered by a configurable multi-provider LLM gateway with your own keys (BYOK).",
  },
  {
    icon: ShieldCheck,
    title: "Private & Secure",
    desc: "Your documents are stored in encrypted private storage, accessible only to you.",
  },
  {
    icon: Sparkles,
    title: "Skill Gap Analysis",
    desc: "Identifies missing and weak skills, then recommends a tailored learning plan.",
  },
];

export default function Home() {
  const { user } = useAuth();
  const [health, setHealth] = useState<string>("Checking…");
  const [ok, setOk] = useState<boolean | null>(null);

  useEffect(() => {
    apiGet<HealthResponse>("/health")
      .then((data) => {
        setOk(true);
        setHealth(`${data.app} — database: ${data.database}`);
      })
      .catch((e) => {
        setOk(false);
        setHealth(errMsg(e));
      });
  }, []);

  return (
    <div className="fade-in">
      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className="mb-12">
        <span
          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium mb-4"
          style={{
            background: "var(--color-brand-soft)",
            color: "var(--color-brand)",
          }}
        >
          <Sparkles size={13} />
          AI-powered candidate screening
        </span>
        <h1
          className="text-4xl md:text-5xl font-bold leading-tight mb-4"
          style={{ color: "var(--color-text)" }}
        >
          Find the right candidate,
          <br />
          <span style={{ color: "var(--color-brand)" }}>in seconds.</span>
        </h1>
        <p className="text-lg max-w-2xl mb-6" style={{ color: "var(--color-text-muted)" }}>
          Agentic Resume Screening parses resumes, matches them against job
          descriptions, and surfaces missing skills with personalized learning
          plans — automatically.
        </p>
        <div className="flex flex-wrap gap-3">
          {user ? (
            <Link
              to="/screen"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium no-underline"
              style={{
                background: "var(--color-brand)",
                color: "#fff",
              }}
            >
              Screen a resume now
              <ArrowRight size={16} />
            </Link>
          ) : (
            <Link
              to="/login"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium no-underline"
              style={{
                background: "var(--color-brand)",
                color: "#fff",
              }}
            >
              Get started
              <ArrowRight size={16} />
            </Link>
          )}
          <Link
            to="/screen"
            className="px-5 py-2.5 rounded-lg font-medium no-underline"
            style={{
              background: "var(--color-brand-soft)",
              color: "var(--color-brand)",
            }}
          >
            Try the demo
          </Link>
        </div>
      </section>

      {/* ── Feature cards ────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-12">
        {features.map((s) => (
          <Link
            key={s.to}
            to={s.to}
            className="panel no-underline hover:shadow-md transition-shadow"
          >
            <span
              className="w-11 h-11 rounded-lg flex items-center justify-center mb-3"
              style={{ background: "var(--color-brand-soft)" }}
            >
              <s.icon size={22} style={{ color: "var(--color-brand)" }} />
            </span>
            <h2 className="text-base font-semibold mb-1" style={{ color: "var(--color-text)" }}>
              {s.title}
            </h2>
            <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
              {s.desc}
            </p>
          </Link>
        ))}
      </div>

      {/* ── Highlights ───────────────────────────────────────── */}
      <section className="mb-12">
        <h2
          className="text-2xl font-bold mb-6"
          style={{ color: "var(--color-text)" }}
        >
          Why AetherGate
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {highlights.map((h) => (
            <div key={h.title} className="panel">
              <span
                className="w-10 h-10 rounded-lg flex items-center justify-center mb-3"
                style={{ background: "var(--color-brand-soft)" }}
              >
                <h.icon size={20} style={{ color: "var(--color-brand)" }} />
              </span>
              <h3 className="font-semibold mb-1" style={{ color: "var(--color-text)" }}>
                {h.title}
              </h3>
              <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
                {h.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Health ───────────────────────────────────────────── */}
      <div className="panel">
        <h2 className="text-base font-semibold mb-2" style={{ color: "var(--color-text)" }}>
          API Health
        </h2>
        <div
          className="text-sm flex items-center gap-2"
          style={{ color: "var(--color-text-muted)" }}
        >
          <span
            className="w-2.5 h-2.5 rounded-full"
            style={{
              background:
                ok === null
                  ? "var(--color-warning)"
                  : ok
                    ? "var(--color-success)"
                    : "var(--color-danger)",
            }}
          />
          {health}
        </div>
      </div>
    </div>
  );
}
