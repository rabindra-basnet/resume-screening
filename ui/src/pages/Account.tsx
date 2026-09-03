import { useEffect, useState } from "react";
import { apiGet, errMsg } from "../lib/api";

interface Document {
  id: string;
  resume_filename: string | null;
  resume_blob_url: string | null;
  status: string;
  skill_match_percentage: number;
  created_at: string | null;
}

export default function Account() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await apiGet<Document[]>("/account/documents");
        setDocs(data);
      } catch (err) {
        setError(errMsg(err));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900 mb-6">My Documents</h1>

      {loading && <p className="text-slate-500 text-sm">Loading documents...</p>}
      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      {!loading && docs.length === 0 && (
        <div className="bg-slate-50 rounded-xl border border-slate-200 p-10 text-center">
          <p className="text-slate-500 text-sm mb-2">No documents yet</p>
          <p className="text-slate-400 text-xs">
            Upload a resume on the <a href="/screen" className="text-blue-600 hover:underline">Screen Resume</a> page.
          </p>
        </div>
      )}

      {docs.length > 0 && (
        <div className="space-y-3">
          {docs.map((doc) => (
            <div
              key={doc.id}
              className="bg-white rounded-xl border border-slate-200 p-4 flex items-center justify-between"
            >
              <div>
                <p className="text-sm font-medium text-slate-900">
                  {doc.resume_filename || "Unnamed document"}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">
                  {doc.status} · {doc.skill_match_percentage.toFixed(1)}% match
                  {doc.created_at && (
                    <> · {new Date(doc.created_at).toLocaleDateString()}</>
                  )}
                </p>
              </div>
              <div className="flex gap-2">
                {doc.resume_blob_url && (
                  <a
                    href={doc.resume_blob_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs bg-slate-100 text-slate-700 px-3 py-1.5 rounded-lg hover:bg-slate-200 transition-colors"
                  >
                    Download
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
