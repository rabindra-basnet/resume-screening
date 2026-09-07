import type { LearningResource } from "@/shared/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { BookOpen, ExternalLink, Clock } from "lucide-react";

interface ResourceGroupProps {
  skill: string;
  items: LearningResource[];
}

export function ResourceGroupCard({ skill, items }: ResourceGroupProps) {
  return (
    <Card className="border-border/60 bg-card/90 backdrop-blur overflow-hidden shadow-sm">
      <CardHeader className="bg-muted/30 pb-3 border-b border-border/40">
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2 font-bold">
            <BookOpen size={18} className="text-primary" />
            {skill}
          </span>
          <Badge variant="secondary" className="text-xs font-semibold">
            {items.length} {items.length === 1 ? "resource" : "resources"}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0 divide-y divide-border/40">
        {items.map((r, i) => (
          <div
            key={i}
            className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-muted/20 transition-colors"
          >
            <div className="space-y-1 max-w-3xl">
              <div className="flex items-center gap-2 flex-wrap">
                <a
                  href={r.url || "#"}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-semibold text-base text-foreground hover:text-primary no-underline flex items-center gap-1.5 transition-colors"
                >
                  {r.title}
                  <ExternalLink size={14} className="text-muted-foreground" />
                </a>
              </div>
              {r.description && (
                <p className="text-sm text-muted-foreground leading-relaxed line-clamp-2">
                  {r.description}
                </p>
              )}
              <div className="flex items-center gap-3 text-xs text-muted-foreground pt-1">
                {r.provider && (
                  <span className="font-medium text-foreground">{r.provider}</span>
                )}
                {r.estimated_hours && (
                  <span className="flex items-center gap-1">
                    <Clock size={12} /> ~{r.estimated_hours}h estimated
                  </span>
                )}
                {r.resource_type && (
                  <Badge variant="outline" className="text-[10px] uppercase tracking-wider py-0">
                    {r.resource_type}
                  </Badge>
                )}
              </div>
            </div>

            <a
              href={r.url || "#"}
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0"
            >
              <Button variant="outline" size="sm" className="gap-1.5 rounded-lg w-full sm:w-auto">
                Open Link <ExternalLink size={12} />
              </Button>
            </a>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
