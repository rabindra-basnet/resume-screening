import { useState } from "react";
import { apiGet, apiPost, errMsg } from "../lib/api";
import type { JobDescription } from "../lib/types";

const inputClass =
  "w-full px-3 py-2 rounded-lg text-sm focus:outline-none transition-colors";

export default function Jobs() {
  const [title, setTitle] = useState("");
  const [rawText, setRawText] = useState("");
  const [submitBtn, setSubmitBtn] = useState("Create");
  const [createResult, setCreateResult] = useState<React.ReactNode>(null);

  const [jdId, setJdId] = useState("");
  const [jdView, setJdView] = useState<React.ReactNode>(null);

  const fieldStyle = {
    background: "var(--color-app-surface)",
    border: "1px solid var(--color-border)",
    color: "var(--color-text)",
  };

  const createJD = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitBtn("Creating…");
    try {
      const data = await apiPost<JobDescription>("/job-descriptions", {
        title,
        raw_text: rawText,
      });
      setCreateResult(
        <div className="panel">
          <p className="text-sm">
            <strong style={{ color: "var(--color-success)" }}>Created!</strong>{" "}
            ID: <code>{data.id}</code>
          </p>
          <p className="text-sm mt-2" style={{ color: "var(--color-text-muted)" }}>
            {data.title || "Untitled"} — {data.skills?.length || 0} skills extracted
          </p>
        </div>,
      );
      setTitle("");
      setRawText("");
    } catch (e) {
      setCreateResult(<p className="text-sm" style={{ color: "var(--color-danger)" }}>{errMsg(e)}</p>);
    } finally {
      setSubmitBtn("Create");
    }
  };

  const fetchJD = async () => {
    if (!jdId.trim()) return;
    setJdView(<div className="spinner" />);
    try {
      const data = await apiGet<JobDescription>(`/job-descriptions/${jdId}`);
      setJdView(
        <div className="panel">
          <h2 className="text-base font-semibold mb-2 text-text">{data.title || "Untitled"}</h2>
          <div className="meta-row">
            <span className="meta-label">ID</span>
            <span>{data.id}</span>
          </div>
          {data.min_work_experience != null && (
            <div className="meta-row">
              <span className="meta-label">Min Experience</span>
              <span>{data.min_work_experience} years</span>
            </div>
          )}
          {data.max_work_experience != null && (
            <div className="meta-row">
              <span className="meta-label">Max Experience</span>
              <span>{data.max_work_experience} years</span>
            </div>
          )}
          <div className="mt-3">
            <strong>Skills:</strong>
            <div className="flex flex-wrap gap-1.5 mt-1.5">
              {(data.skills || []).map((s) => (
                <span key={s} className="px-2.5 py-1 rounded-full text-xs font-medium" style={{ background: "var(--color-info-soft)", color: "var(--color-info)" }}>
                  {s}
                </span>
              ))}
            </div>
          </div>
          <div className="mt-3">
            <strong>Raw Text:</strong>
            <pre className="whitespace-pre-wrap text-sm mt-1.5" style={{ color: "var(--color-text-muted)" }}>
              {data.raw_text}
            </pre>
          </div>
        </div>,
      );
    } catch (e) {
      setJdView(<p className="text-sm" style={{ color: "var(--color-danger)" }}>{errMsg(e)}</p>);
    }
  };

  return (
    <div className="fade-in">
      <h1 className="text-2xl font-bold mb-5" style={{ color: "var(--color-text)" }}>
        Job Descriptions
      </h1>

      <div className="panel">
        <h2 className="text-base font-semibold mb-4 text-text">Create New Job Description</h2>
        <form onSubmit={createJD}>
          <div className="mb-4">
            <label className="label" htmlFor="title">Job Title</label>
            <input
              id="title"
              className={inputClass}
              style={fieldStyle}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              placeholder="e.g. Senior Software Engineer"
            />
          </div>
          <div className="mb-4">
            <label className="label" htmlFor="raw_text">Job Description</label>
            <textarea
              id="raw_text"
              className={`${inputClass} resize-y min-h-[140px]`}
              style={fieldStyle}
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              required
              placeholder="Paste the full job description here…"
            />
          </div>
          <button type="submit" disabled={submitBtn !== "Create"} className="btn btn-primary">
            {submitBtn}
          </button>
        </form>
        {createResult && <div className="mt-4">{createResult}</div>}
      </div>

      <div className="panel mt-5">
        <h2 className="text-base font-semibold mb-4 text-text">View Job Description</h2>
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
        <button onClick={fetchJD} className="btn btn-secondary">Fetch</button>
        {jdView && <div className="mt-4">{jdView}</div>}
      </div>
    </div>
  );
}
