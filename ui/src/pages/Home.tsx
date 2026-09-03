import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet, errMsg } from "../lib/api";
import type { HealthResponse } from "../lib/types";
import { Briefcase, Upload, GraduationCap } from "lucide-react";

const sections = [
  {
    to: "/jobs",
    title: "Job Descriptions",
    desc: "Create and manage job descriptions for screening.",
    icon: Briefcase,
  },
  {
    to: "/screen",
    title: "Screen Resume",
    desc: "Upload a resume and match it against a job description.",
    icon: Upload,
  },
  {
    to: "/learning",
    title: "Learning Center",
    desc: "Resources recommended to close skill gaps.",
    icon: GraduationCap,
  },
];

export default function Home() {
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
      <section className="mb-8">
        <h1
          className="text-3xl font-bold mb-1"
          style={{ color: "var(--color-text)" }}
        >
          Agentic Resume Screening
        </h1>
        <p className="text-base" style={{ color: "var(--color-text-muted)" }}>
          AI-powered candidate screening and matching against job descriptions.
        </p>
      </section>

      <div
        className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8"
      >
        {sections.map((s) => (
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

      <div className="panel">
        <h2 className="text-base font-semibold mb-2" style={{ color: "var(--color-text)" }}>
          API Health
        </h2>
        <div className="text-sm flex items-center gap-2" style={{ color: "var(--color-text-muted)" }}>
          <span
            className="w-2.5 h-2.5 rounded-full"
            style={{
              background:
                ok === null ? "var(--color-warning)" : ok ? "var(--color-success)" : "var(--color-danger)",
            }}
          />
          {health}
        </div>
      </div>
    </div>
  );
}
