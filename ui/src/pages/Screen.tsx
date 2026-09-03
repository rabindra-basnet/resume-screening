import { useRef, useState } from "react";
import { apiUpload, errMsg } from "../lib/api";
import type { ScreeningCandidate, ScreeningEvaluation, ScreeningResult } from "../lib/types";
import { UploadCloud } from "lucide-react";

const inputClass = "w-full px-3 py-2 rounded-lg text-sm focus:outline-none transition-colors";

const fieldStyle = {
  background: "var(--color-app-surface)",
  border: "1px solid var(--color-border)",
  color: "var(--color-text)",
} as const;

const statusStyle: Record<string, string> = {
  selected: "success",
  rejected: "danger",
  pending: "warning",
};

export default function Screen() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [jdSource, setJdSource] = useState<"existing" | "inline">("existing");
  const [jdId, setJdId] = useState("");
  const [jdText, setJdText] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<React.ReactNode>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const selectFile = (file: File) => setSelectedFile(file);

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files.length) selectFile(e.dataTransfer.files[0]);
  };

  const screen = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      alert("Please select a PDF or DOCX resume");
      return;
    }
    const formData = new FormData();
    formData.append("resume", selectedFile);
    if (jdSource === "existing") {
      if (!jdId.trim()) {
        alert("Enter a JD ID");
        return;
      }
      formData.append("jd_id", jdId.trim());
    } else {
      if (!jdText.trim()) {
        alert("Enter job description text");
        return;
      }
      formData.append("job_description", jdText);
    }

    setBusy(true);
    setResult(
      <div className="panel">
        <span className="spinner inline-block align-middle mr-2" />
        Analyzing resume…
      </div>,
    );

    try {
      const data = await apiUpload<ScreeningResult>("/screening", formData);
      setResult(renderResult(data));
    } catch (err) {
      setResult(
        <div className="panel">
          <p style={{ color: "var(--color-danger)" }}>{errMsg(err)}</p>
        </div>,
      );
    } finally {
      setBusy(false);
    }
  };

  const renderResult = (data: ScreeningResult) => {
    const c: ScreeningCandidate = data.candidate ?? ({} as ScreeningCandidate);
    const e: ScreeningEvaluation = data.evaluation ?? ({} as ScreeningEvaluation);
    const status = e.candidate_status || "pending";
    const tone = statusStyle[status] || "warning";

    return (
      <div className="panel">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-text">{c.name || "Unknown Candidate"}</h2>
          <span
            className="px-2.5 py-1 rounded-full text-xs font-semibold uppercase"
            style={{
              background: `var(--color-${tone}-soft)`,
              color: `var(--color-${tone})`,
            }}
          >
            {status}
          </span>
        </div>

        {c.email && <MetaRow label="Email" value={c.email} />}
        {c.phone && <MetaRow label="Phone" value={c.phone} />}
        {e.experience_years != null && (
          <MetaRow label="Experience" value={`${e.experience_years} years`} />
        )}

        <div className="mt-4">
          <strong className="text-sm">Skill Match: {e.skill_match_percentage || 0}%</strong>
          <div
            className="w-full h-2 rounded overflow-hidden mt-2"
            style={{ background: "var(--color-border)" }}
          >
            <div
              className="h-full rounded transition-all"
              style={{
                width: `${e.skill_match_percentage || 0}%`,
                background: "var(--color-brand)",
              }}
            />
          </div>
        </div>

        {e.matched_skills?.length ? (
          <SkillGroup title="Matched Skills" skills={e.matched_skills} tone="success" />
        ) : null}
        {e.missing_skills?.length ? (
          <SkillGroup title="Missing Skills" skills={e.missing_skills} tone="danger" />
        ) : null}
        {e.weak_skills?.length ? (
          <SkillGroup title="Weak Skills (need strengthening)" skills={e.weak_skills} tone="warning" />
        ) : null}

        {data.learning_plan && renderLearningPlan(data.learning_plan)}

        {e.reason ? (
          <div className="mt-4">
            <strong className="text-sm">Reason</strong>
            <p className="text-sm mt-1" style={{ color: "var(--color-text-muted)" }}>
              {e.reason}
            </p>
          </div>
        ) : null}

        {c.education?.length ? (
          <div className="mt-4">
            <strong className="text-sm">Education</strong>
            {c.education.map((ed, i) => (
              <p key={i} className="text-sm" style={{ color: "var(--color-text-muted)" }}>
                {ed.degree || ""}
                {ed.field_of_study ? ` in ${ed.field_of_study}` : ""} — {ed.institution || ""}
              </p>
            ))}
          </div>
        ) : null}

        {c.work_history?.length ? (
          <div className="mt-4">
            <strong className="text-sm">Work History</strong>
            {c.work_history.map((w, i) => (
              <p key={i} className="text-sm" style={{ color: "var(--color-text-muted)" }}>
                {w.title || ""} at {w.company || ""} ({w.years || "?"} years)
              </p>
            ))}
          </div>
        ) : null}

        {data.model_used ? <MetaRow label="Model" value={data.model_used} /> : null}
      </div>
    );
  };

  const renderLearningPlan = (lp: NonNullable<ScreeningResult["learning_plan"]>) => {
    const gaps = lp.skill_gaps || [];
    const resources = lp.resources || [];
    if (!gaps.length) return null;
    return (
      <div className="panel mt-5" style={{ borderColor: "var(--color-brand-strong, var(--color-brand))" }}>
        <h2 className="text-base font-semibold mb-1 flex items-center justify-between text-text">
          <span>Recommended Learning Plan</span>
          {lp.total_estimated_hours ? (
            <span className="text-sm font-normal" style={{ color: "var(--color-text-muted)" }}>
              ~{lp.total_estimated_hours}h
            </span>
          ) : null}
        </h2>
        <p className="text-sm mb-3" style={{ color: "var(--color-text-muted)" }}>
          Based on the skills you&apos;re missing or need to strengthen for this role.
        </p>
        {resources.length ? (
          <div className="flex flex-wrap gap-2.5">
            {resources.map((r, i) => (
              <a
                key={i}
                href={r.url || "#"}
                target="_blank"
                rel="noopener noreferrer"
                className="panel no-underline block !p-3 !mb-0 hover:shadow-md transition-shadow"
                style={{ maxWidth: 320 }}
              >
                <span className="block text-[10px] uppercase tracking-wide font-bold" style={{ color: "var(--color-brand)" }}>
                  {r.skill}
                </span>
                <span className="block text-[13px] font-semibold mt-1 text-text">{r.title}</span>
                <span className="block text-[11px] mt-0.5" style={{ color: "var(--color-text-muted)" }}>
                  {r.provider || ""}
                  {r.estimated_hours ? ` · ${r.estimated_hours}h` : ""}
                </span>
              </a>
            ))}
          </div>
        ) : null}
      </div>
    );
  };

  return (
    <div className="fade-in">
      <h1 className="text-2xl font-bold mb-5" style={{ color: "var(--color-text)" }}>
        Screen Resume
      </h1>

      <div className="panel">
        <form onSubmit={screen}>
          <div className="mb-5">
            <label className="label">Resume (PDF or DOCX)</label>
            <div
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              className="border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors"
              style={{
                borderColor: dragging ? "var(--color-brand)" : "var(--color-border-strong)",
                background: dragging ? "var(--color-brand-soft)" : "var(--color-app-surface-alt)",
              }}
            >
              <UploadCloud
                size={32}
                className="mx-auto mb-2"
                style={{ color: "var(--color-brand)" }}
              />
              <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
                {selectedFile
                  ? selectedFile.name
                  : "Drop PDF or DOCX here, or click to select"}
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx"
                hidden
                onChange={(e) => {
                  if (e.target.files?.length) selectFile(e.target.files[0]);
                }}
              />
            </div>
          </div>

          <div className="mb-4">
            <label className="label" htmlFor="jd-source">Job Description Source</label>
            <select
              id="jd-source"
              className={inputClass}
              style={fieldStyle}
              value={jdSource}
              onChange={(e) => setJdSource(e.target.value as "existing" | "inline")}
            >
              <option value="existing">Use existing Job Description</option>
              <option value="inline">Paste Job Description</option>
            </select>
          </div>

          {jdSource === "existing" ? (
            <div className="mb-4">
              <label className="label" htmlFor="jd-id">Job Description ID</label>
              <input
                id="jd-id"
                className={inputClass}
                style={fieldStyle}
                value={jdId}
                onChange={(e) => setJdId(e.target.value)}
                placeholder="Enter JD ID"
              />
            </div>
          ) : (
            <div className="mb-4">
              <label className="label" htmlFor="jd-text">Job Description Text</label>
              <textarea
                id="jd-text"
                className={`${inputClass} resize-y min-h-[140px]`}
                style={fieldStyle}
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                placeholder="Paste job description here…"
              />
            </div>
          )}

          <button type="submit" disabled={busy} className="btn btn-primary">
            {busy ? (
              <span className="inline-flex items-center gap-2">
                <span className="spinner" /> Screening…
              </span>
            ) : (
              "Screen Resume"
            )}
          </button>
        </form>
      </div>

      {result && <div className="mt-5">{result}</div>}
    </div>
  );
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="meta-row text-sm" style={{ borderColor: "var(--color-border)" }}>
      <span style={{ color: "var(--color-text-muted)" }}>{label}</span>
      <span style={{ color: "var(--color-text)" }}>{value}</span>
    </div>
  );
}

function SkillGroup({
  title,
  skills,
  tone,
}: {
  title: string;
  skills: string[];
  tone: "success" | "danger" | "warning";
}) {
  return (
    <div className="mt-3">
      <strong className="text-sm">{title}</strong>
      <div className="flex flex-wrap gap-1.5 mt-1.5">
        {skills.map((s) => (
          <span
            key={s}
            className="px-2.5 py-1 rounded-full text-xs font-medium"
            style={{ background: `var(--color-${tone}-soft)`, color: `var(--color-${tone})` }}
          >
            {s}
          </span>
        ))}
      </div>
    </div>
  );
}
