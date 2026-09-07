import { useState, useEffect } from "react";
import { Link } from "@tanstack/react-router";
import { apiGet, errMsg } from "@/shared/api/client";
import { Card, CardContent } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { Input } from "@/shared/components/ui/input";
import { FileText, Upload, Search } from "lucide-react";
import { AccountMetrics, type AccountDocument } from "../components/AccountMetrics";
import { DocumentCard } from "../components/DocumentCard";

export default function AccountPage() {
  const [docs, setDocs] = useState<AccountDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  useEffect(() => {
    let isMounted = true;
    (async () => {
      try {
        const data = await apiGet<AccountDocument[]>("/account/documents");
        if (isMounted) setDocs(data || []);
      } catch (err) {
        if (isMounted) setError(errMsg(err));
      } finally {
        if (isMounted) setLoading(false);
      }
    })();
    return () => {
      isMounted = false;
    };
  }, []);

  const filteredDocs = docs.filter((doc) => {
    const matchesSearch = (doc.resume_filename || "unnamed")
      .toLowerCase()
      .includes(search.toLowerCase());
    const matchesFilter =
      statusFilter === "all" || doc.status?.toLowerCase() === statusFilter.toLowerCase();
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="space-y-8 fade-in">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">My Documents</h1>
          <p className="text-muted-foreground mt-1">
            Manage your uploaded resumes, screening results, and processed candidates.
          </p>
        </div>
        <Link to="/screen">
          <Button className="gap-2 shadow-sm">
            <Upload size={16} />
            Screen New Resume
          </Button>
        </Link>
      </div>

      <AccountMetrics docs={docs} />

      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
          <Input
            placeholder="Search documents..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 bg-card"
          />
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto">
          {["all", "selected", "pending", "rejected"].map((filter) => (
            <Button
              key={filter}
              variant={statusFilter === filter ? "default" : "outline"}
              size="sm"
              onClick={() => setStatusFilter(filter)}
              className="capitalize text-xs rounded-lg"
            >
              {filter}
            </Button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="space-y-3">
          <Skeleton className="h-20 w-full rounded-2xl" />
          <Skeleton className="h-20 w-full rounded-2xl" />
          <Skeleton className="h-20 w-full rounded-2xl" />
        </div>
      )}

      {error && (
        <Card className="border-destructive/30 bg-destructive/5">
          <CardContent className="p-6 text-center text-sm text-destructive">
            {error}
          </CardContent>
        </Card>
      )}

      {!loading && !error && filteredDocs.length === 0 && (
        <Card className="border-dashed border-border/80 bg-card/40">
          <CardContent className="py-14 text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
              <FileText size={24} />
            </div>
            <h3 className="text-lg font-semibold">No documents found</h3>
            <p className="mt-1 text-sm text-muted-foreground max-w-sm mx-auto">
              {search || statusFilter !== "all"
                ? "Try adjusting your search query or status filter."
                : "Upload a candidate's resume to start automated screening."}
            </p>
            {!search && statusFilter === "all" && (
              <Link to="/screen" className="mt-5 inline-block">
                <Button size="sm" className="gap-2">
                  <Upload size={14} /> Screen First Resume
                </Button>
              </Link>
            )}
          </CardContent>
        </Card>
      )}

      {!loading && filteredDocs.length > 0 && (
        <div className="grid gap-3">
          {filteredDocs.map((doc) => (
            <DocumentCard key={doc.id} doc={doc} />
          ))}
        </div>
      )}
    </div>
  );
}
