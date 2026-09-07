import { Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useNavigate, useSearch } from "@tanstack/react-router";
import { apiGet, errMsg } from "@/shared/api/client";
import type { LearningResource } from "@/shared/types";
import { Card, CardContent } from "@/shared/components/ui/card";
import { Input } from "@/shared/components/ui/input";
import { Button } from "@/shared/components/ui/button";
import { Badge } from "@/shared/components/ui/badge";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { GraduationCap, Search, Sparkles, Filter, Upload, Briefcase } from "lucide-react";
import { ResourceGroupCard } from "../components/ResourceCard";

export default function LearningPage() {
  const navigate = useNavigate();
  const searchParams = useSearch({ from: "/_workspace/learning" });
  const [query, setQuery] = useState(searchParams.q || "");
  const [resources, setResources] = useState<LearningResource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("All");

  const fetchResources = async (searchQuery: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<{ resources: LearningResource[] }>("/learning?limit=200");
      let list = data.resources || [];
      if (searchQuery.trim()) {
        const needle = searchQuery.toLowerCase();
        list = list.filter(
          (r) =>
            (r.skill || "").toLowerCase().includes(needle) ||
            (r.title || "").toLowerCase().includes(needle) ||
            (r.provider || "").toLowerCase().includes(needle)
        );
      }
      setResources(list);
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResources(searchParams.q || "");
  }, [searchParams.q]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    navigate({
      to: "/learning",
      search: (old) => ({ ...old, q: query.trim() || undefined }),
    });
  };

  const categories = ["All", ...Array.from(new Set(resources.map((r) => r.skill || "General")))];

  const filteredResources = selectedCategory === "All"
    ? resources
    : resources.filter((r) => (r.skill || "General") === selectedCategory);

  const bySkill: Record<string, LearningResource[]> = {};
  filteredResources.forEach((r) => {
    const key = r.skill || "General";
    (bySkill[key] = bySkill[key] || []).push(r);
  });

  return (
    <div className="space-y-8 fade-in">
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
          <Sparkles size={13} /> Agentic Talent Workspace
        </div>
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
          Learning Roadmap
        </h1>
        <p className="max-w-2xl text-muted-foreground">
          Targeted courses, tutorials, and materials recommended to close skill gaps discovered during candidate resume screenings.
        </p>
      </div>

      {/* Single Workspace Navigation Tabs */}
      <div className="flex items-center justify-between border-b border-border/60">
        <div className="flex items-center gap-1">
          <Link
            to="/screen"
            activeProps={{
              className: "border-primary text-primary font-bold",
            }}
            inactiveProps={{
              className: "border-transparent text-muted-foreground hover:text-foreground",
            }}
            className="flex items-center gap-2 rounded-t-lg border-b-2 px-4 py-2.5 font-semibold text-sm transition-all"
          >
            <Upload size={16} /> Screen Resume
          </Link>
          <Link
            to="/jobs"
            activeProps={{
              className: "border-primary text-primary font-bold",
            }}
            inactiveProps={{
              className: "border-transparent text-muted-foreground hover:text-foreground",
            }}
            className="flex items-center gap-2 rounded-t-lg border-b-2 px-4 py-2.5 font-semibold text-sm transition-all"
          >
            <Briefcase size={16} /> Job Descriptions
          </Link>
          <Link
            to="/learning"
            activeProps={{
              className: "border-primary text-primary font-bold",
            }}
            inactiveProps={{
              className: "border-transparent text-muted-foreground hover:text-foreground",
            }}
            className="flex items-center gap-2 rounded-t-lg border-b-2 px-4 py-2.5 font-semibold text-sm transition-all"
          >
            <GraduationCap size={16} /> Learning Roadmap
          </Link>
        </div>
      </div>

      <Card className="border-border/60 bg-card/80 backdrop-blur shadow-sm">
        <CardContent className="p-4">
          <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row items-center gap-3">
            <div className="relative flex-1 w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search resources by skill (e.g. Python, Docker, React)..."
                className="pl-9 bg-background/50"
              />
            </div>
            <div className="flex gap-2 w-full sm:w-auto">
              <Button type="submit" className="flex-1 sm:flex-initial gap-2">
                <Search size={14} /> Search
              </Button>
              {searchParams.q && (
                <Button
                  variant="ghost"
                  onClick={() => {
                    setQuery("");
                    navigate({ to: "/learning", search: (old) => ({ ...old, q: undefined }) });
                  }}
                >
                  Clear
                </Button>
              )}
            </div>
          </form>

          {!loading && categories.length > 2 && (
            <div className="mt-4 flex items-center gap-1.5 overflow-x-auto pt-2 border-t border-border/40">
              <span className="text-xs text-muted-foreground font-medium mr-2 flex items-center gap-1">
                <Filter size={12} /> Skills:
              </span>
              {categories.map((cat) => (
                <Badge
                  key={cat}
                  variant={selectedCategory === cat ? "default" : "outline"}
                  className="cursor-pointer capitalize text-xs rounded-lg px-2.5 py-1 font-medium transition-all"
                  onClick={() => setSelectedCategory(cat)}
                >
                  {cat}
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {loading && (
        <div className="space-y-4">
          <Skeleton className="h-28 w-full rounded-2xl" />
          <Skeleton className="h-28 w-full rounded-2xl" />
        </div>
      )}

      {error && (
        <Card className="border-destructive/30 bg-destructive/5">
          <CardContent className="p-6 text-center text-sm text-destructive">
            {error}
          </CardContent>
        </Card>
      )}

      {!loading && !error && filteredResources.length === 0 && (
        <Card className="border-dashed border-border/80 bg-card/40">
          <CardContent className="py-14 text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
              <GraduationCap size={24} />
            </div>
            <h3 className="text-lg font-semibold">No learning resources found</h3>
            <p className="mt-1 text-sm text-muted-foreground max-w-md mx-auto">
              {searchParams.q
                ? `No resources matching "${searchParams.q}". Try searching for another skill.`
                : "Run a resume screening to automatically generate personalized learning plans."}
            </p>
          </CardContent>
        </Card>
      )}

      {!loading && !error && Object.keys(bySkill).length > 0 && (
        <div className="space-y-6">
          {Object.entries(bySkill).map(([skill, items]) => (
            <ResourceGroupCard key={skill} skill={skill} items={items} />
          ))}
        </div>
      )}
    </div>
  );
}
