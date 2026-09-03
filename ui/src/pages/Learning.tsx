import { useEffect, useState } from "react";
import { apiGet, errMsg } from "../lib/api";
import type { LearningResource } from "../lib/types";

const inputClass = "flex-1 px-3 py-2 rounded-lg text-sm focus:outline-none transition-colors";
const fieldStyle = {
  background: "var(--color-app-surface)",
  border: "1px solid var(--color-border)",
  color: "var(--color-text)",
} as const;

export default function Learning() {
  const [search, setSearch] = useState("");
  const [content, setContent] = useState<React.ReactNode>(<div className="spinner" />);

  const loadResources = async (applyFilter: boolean) => {
    const q = search.trim();
    const query = q ? "?limit=200" : "";
    setContent(
      <div className="panel">
        <span className="spinner inline-block align-middle mr-2" />
        Loading resources…
      </div>,
    );
    try {
      const data = await apiGet<{ resources: LearningResource[] }>("/learning" + query);
      let resources = data.resources || [];
      if (applyFilter && q) {
        const needle = q.toLowerCase();
        resources = resources.filter(
          (r) =>
            (r.skill || "").toLowerCase().includes(needle) ||
            (r.title || "").toLowerCase().includes(needle),
        );
      }
      renderResources(resources);
    } catch (e) {
      setContent(<p style={{ color: "var(--color-danger)" }}>{errMsg(e)}</p>);
    }
  };

  const renderResources = (resources: LearningResource[]) => {
    if (!resources.length) {
      setContent(
        <div className="text-center py-12" style={{ color: "var(--color-text-muted)" }}>
          No learning resources yet. Run a screening to generate a learning plan.
        </div>,
      );
      return;
    }
    const bySkill: Record<string, LearningResource[]> = {};
    resources.forEach((r) => {
      const key = r.skill || "Other";
      (bySkill[key] = bySkill[key] || []).push(r);
    });
    setContent(
      <>
        {Object.entries(bySkill).map(([skill, rows]) => (
          <div className="panel" key={skill}>
            <h2 className="text-base font-semibold mb-3 flex items-center gap-2 text-text">
              {skill}
              <span
                className="inline-block rounded-full text-xs font-semibold px-2 py-0.5"
                style={{ background: "var(--color-info-soft)", color: "var(--color-info)" }}
              >
                {rows.length}
              </span>
            </h2>
            {rows.map((r, i) => (
              <div
                key={i}
                className="flex justify-between items-start gap-3 py-2.5"
                style={{ borderBottom: i < rows.length - 1 ? "1px solid var(--color-border)" : "none" }}
              >
                <div>
                  <a
                    href={r.url || "#"}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="no-underline font-semibold text-[13px] hover:underline"
                    style={{ color: "var(--color-text)" }}
                  >
                    {r.title}
                  </a>
                  <div className="text-xs mt-0.5" style={{ color: "var(--color-text-muted)" }}>
                    {r.provider || ""}
                    {r.estimated_hours ? ` · ~${r.estimated_hours}h` : ""}
                    {r.resource_type ? ` · ${r.resource_type}` : ""}
                  </div>
                  {r.description ? (
                    <p className="text-sm mt-1" style={{ color: "var(--color-text-muted)" }}>
                      {r.description}
                    </p>
                  ) : null}
                </div>
                <span
                  className="text-[11px] rounded px-1.5 py-0.5 whitespace-nowrap"
                  style={{
                    color: "var(--color-text-muted)",
                    background: "var(--color-app-surface-alt)",
                  }}
                >
                  {r.screening_id ? r.screening_id.slice(0, 8) : ""}
                </span>
              </div>
            ))}
          </div>
        ))}
      </>,
    );
  };

  useEffect(() => {
    loadResources(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="fade-in">
      <h1 className="text-2xl font-bold mb-1" style={{ color: "var(--color-text)" }}>
        Learning Center
      </h1>
      <p className="mb-5" style={{ color: "var(--color-text-muted)" }}>
        Resources recommended to close skill gaps identified during resume screenings.
      </p>

      <div className="panel flex gap-2.5 items-center !py-3.5">
        <input
          className={inputClass}
          style={fieldStyle}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && loadResources(true)}
          placeholder="Filter by skill or title…"
        />
        <button onClick={() => loadResources(true)} className="btn btn-primary">
          Search
        </button>
      </div>

      <div className="mt-5">{content}</div>
    </div>
  );
}
