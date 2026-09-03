import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet, errMsg } from "../lib/api";
import type { HealthResponse } from "../lib/types";
import { Upload, ArrowRight, FileText, TrendingUp } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

const steps = [
  {
    n: "01",
    title: "Paste the job",
    desc: "Drop the job description in. If it's saved, pick it from the list.",
  },
  {
    n: "02",
    title: "Upload a resume",
    desc: "PDF or DOCX. The parser pulls out profile, skills, and work history.",
  },
  {
    n: "03",
    title: "Get a match read",
    desc: "A score, the skills that line up, the ones that don't, and what's missing.",
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
      {/* Hero */}
      <section className="mb-12">
        <h1
          className="text-4xl md:text-5xl font-bold leading-tight mb-4"
          style={{ color: "var(--color-text)" }}
        >
          Does this resume actually
          <br />
          fit the job you're hiring for?
          <span style={{ color: "var(--color-brand)" }}>.</span>
        </h1>
        <p className="text-lg max-w-2xl mb-6" style={{ color: "var(--color-text-muted)" }}>
          Paste a job description, upload a resume, and get a straight answer:
          a match score, the experience that carries the candidate, the gaps
          that would show up in the interview, and what to ask to find out.
        </p>
        <div className="flex flex-wrap gap-3">
          {user ? (
            <Link
              to="/screen"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium no-underline"
              style={{ background: "var(--color-brand)", color: "#fff" }}
            >
              Screen a resume
              <ArrowRight size={16} />
            </Link>
          ) : (
            <Link
              to="/login"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium no-underline"
              style={{ background: "var(--color-brand)", color: "#fff" }}
            >
              Sign in with Google
              <ArrowRight size={16} />
            </Link>
          )}
        </div>
        <p className="text-sm mt-4" style={{ color: "var(--color-text-muted)" }}>
          No credit card, no setup. Just a Google account.
        </p>
      </section>

      {/* How it works */}
      <section className="mb-12">
        <h2
          className="text-2xl font-bold mb-6"
          style={{ color: "var(--color-text)" }}
        >
          How it works
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {steps.map((s) => (
            <div key={s.n} className="panel">
              <span
                className="text-xs font-semibold tracking-widest"
                style={{ color: "var(--color-brand)" }}
              >
                {s.n}
              </span>
              <h3
                className="text-base font-semibold mt-1 mb-1"
                style={{ color: "var(--color-text)" }}
              >
                {s.title}
              </h3>
              <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
                {s.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* What you actually get back */}
      <section className="mb-12">
        <h2
          className="text-2xl font-bold mb-6"
          style={{ color: "var(--color-text)" }}
        >
          What you get back
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="panel">
            <FileText size={20} style={{ color: "var(--color-brand)" }} />
            <h3
              className="text-base font-semibold mt-2 mb-1"
              style={{ color: "var(--color-text)" }}
            >
              A score, not a verdict
            </h3>
            <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
              A number that tells you how close the resume is to the post,
              with the reasoning spelled out — not a thumbs up or down.
            </p>
          </div>
          <div className="panel">
            <TrendingUp size={20} style={{ color: "var(--color-brand)" }} />
            <h3
              className="text-base font-semibold mt-2 mb-1"
              style={{ color: "var(--color-text)" }}
            >
              The gaps, named
            </h3>
            <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
              The exact skills and experience the job calls for that the
              resume doesn't show — so you know what to probe in an interview.
            </p>
          </div>
          <div className="panel">
            <Upload size={20} style={{ color: "var(--color-brand)" }} />
            <h3
              className="text-base font-semibold mt-2 mb-1"
              style={{ color: "var(--color-text)" }}
            >
              Want the candidate to improve?
            </h3>
            <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
              The Learning Center turns those gaps into a short list of
              resources so someone can close them.
            </p>
          </div>
        </div>
      </section>

      {/* API Health */}
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
