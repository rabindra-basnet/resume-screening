import { useEffect, useState } from "react";
import { apiGet, errMsg } from "@/shared/api/client";
import type { LearningResource } from "@/shared/types";
import { Card, CardContent } from "@/shared/components/ui/card";
import { Input } from "@/shared/components/ui/input";
import { Button } from "@/shared/components/ui/button";
import { Badge } from "@/shared/components/ui/badge";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { GraduationCap, Search, Filter } from "lucide-react";
import { ResourceGroupCard } from "../components/ResourceCard";

export default function LearningPage() {
  const [query, setQuery] = useState("");
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
    fetchResources(query);
  }, [query]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchResources(query);
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
              {query && (
                <Button
                  variant="ghost"
                  onClick={() => {
                    setQuery("");
                    fetchResources("");
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
              {query
                ? `No resources matching "${query}". Try searching for another skill.`
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
