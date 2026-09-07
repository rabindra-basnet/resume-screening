import { useState } from "react";
import { apiGet, errMsg } from "@/shared/api/client";
import type { JobDescription } from "@/shared/types";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/shared/components/ui/card";
import { Input } from "@/shared/components/ui/input";
import { Button } from "@/shared/components/ui/button";
import { Badge } from "@/shared/components/ui/badge";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { Search, Layers } from "lucide-react";

export function JobLookupView() {
  const [jdId, setJdId] = useState("");
  const [fetching, setFetching] = useState(false);
  const [fetchedJD, setFetchedJD] = useState<JobDescription | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const fetchJD = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!jdId.trim()) return;
    setFetching(true);
    setFetchError(null);
    setFetchedJD(null);
    try {
      const data = await apiGet<JobDescription>(`/job-descriptions/${jdId.trim()}`);
      setFetchedJD(data);
    } catch (e) {
      setFetchError(errMsg(e));
    } finally {
      setFetching(false);
    }
  };

  return (
    <Card className="border-border/60 bg-card/80 backdrop-blur shadow-sm">
      <CardHeader>
        <CardTitle className="text-xl">Fetch Job Description</CardTitle>
        <CardDescription>
          Retrieve existing job requirements and extracted skills using a Job Description ID.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={fetchJD} className="flex gap-3 mb-6">
          <div className="flex-1">
            <Input
              id="jd-id"
              value={jdId}
              onChange={(e) => setJdId(e.target.value)}
              placeholder="Enter JD ID (e.g. 550e8400-e29b-41d4-a716-446655440000)"
              className="bg-background/50"
            />
          </div>
          <Button type="submit" variant="default" disabled={fetching || !jdId.trim()} className="gap-2">
            <Search size={16} /> Fetch
          </Button>
        </form>

        {fetching && (
          <div className="space-y-3">
            <Skeleton className="h-6 w-1/3" />
            <Skeleton className="h-20 w-full" />
          </div>
        )}

        {fetchError && (
          <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/30 text-sm text-destructive">
            {fetchError}
          </div>
        )}

        {fetchedJD && (
          <Card className="border-border/60 bg-card">
            <CardHeader className="pb-3 border-b border-border/40">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg font-bold">
                  {fetchedJD.title || "Untitled Job Description"}
                </CardTitle>
                <code className="rounded bg-muted px-2 py-0.5 font-mono text-xs text-muted-foreground">
                  {fetchedJD.id}
                </code>
              </div>
            </CardHeader>
            <CardContent className="p-5 space-y-4">
              {(fetchedJD.min_work_experience != null || fetchedJD.max_work_experience != null) && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Layers size={16} className="text-primary" />
                  <span>
                    Experience required:{" "}
                    <strong className="text-foreground">
                      {fetchedJD.min_work_experience ?? 0}
                      {fetchedJD.max_work_experience ? ` - ${fetchedJD.max_work_experience}` : "+"} years
                    </strong>
                  </span>
                </div>
              )}

              <div>
                <h4 className="text-sm font-semibold mb-2">Required Skills</h4>
                <div className="flex flex-wrap gap-1.5">
                  {(fetchedJD.skills || []).map((s) => (
                    <Badge key={s} variant="secondary" className="px-2.5 py-1 text-xs font-medium">
                      {s}
                    </Badge>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-sm font-semibold mb-1.5">Raw Text</h4>
                <div className="p-4 rounded-xl bg-muted/40 border border-border/40 text-xs leading-relaxed max-h-60 overflow-y-auto whitespace-pre-wrap text-muted-foreground">
                  {fetchedJD.raw_text}
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </CardContent>
    </Card>
  );
}
