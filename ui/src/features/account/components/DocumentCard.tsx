import type { AccountDocument } from "./AccountMetrics";
import { Card, CardContent } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Badge } from "@/shared/components/ui/badge";
import { FileText, Download, CheckCircle2, XCircle, Clock } from "lucide-react";

const statusBadge: Record<string, { label: string; variant: "default" | "destructive" | "secondary"; icon: typeof CheckCircle2 }> = {
  selected: { label: "Selected", variant: "default", icon: CheckCircle2 },
  rejected: { label: "Rejected", variant: "destructive", icon: XCircle },
  pending: { label: "Pending", variant: "secondary", icon: Clock },
};

export function DocumentCard({ doc }: { doc: AccountDocument }) {
  const statusConfig = statusBadge[doc.status?.toLowerCase()] || {
    label: doc.status || "Unknown",
    variant: "secondary" as const,
    icon: Clock,
  };
  const StatusIcon = statusConfig.icon;

  return (
    <Card className="transition-all hover:border-primary/40 hover:shadow-sm bg-card/80 backdrop-blur">
      <CardContent className="flex flex-col sm:flex-row sm:items-center justify-between p-5 gap-4">
        <div className="flex items-start gap-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <FileText size={22} />
          </div>
          <div>
            <h4 className="text-base font-semibold">
              {doc.resume_filename || "Unnamed Candidate Resume"}
            </h4>
            <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
              <Badge variant={statusConfig.variant} className="gap-1 px-2 py-0.5 text-[11px] font-medium">
                <StatusIcon size={12} />
                {statusConfig.label}
              </Badge>
              <span className="font-semibold text-foreground">
                {doc.skill_match_percentage.toFixed(1)}% match
              </span>
              {doc.created_at && (
                <span>
                  • Uploaded {new Date(doc.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 self-end sm:self-center">
          {doc.resume_blob_url && (
            <a href={doc.resume_blob_url} target="_blank" rel="noopener noreferrer">
              <Button variant="outline" size="sm" className="gap-1.5">
                <Download size={14} />
                Download
              </Button>
            </a>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
