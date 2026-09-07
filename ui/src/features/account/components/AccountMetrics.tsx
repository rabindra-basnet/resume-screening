import { Card, CardContent } from "@/shared/components/ui/card";
import { FileText, CheckCircle2, Clock } from "lucide-react";

export interface AccountDocument {
  id: string;
  resume_filename: string | null;
  resume_blob_url: string | null;
  status: string;
  skill_match_percentage: number;
  created_at: string | null;
}

export function AccountMetrics({ docs }: { docs: AccountDocument[] }) {
  const avgMatch =
    docs.length > 0
      ? (docs.reduce((acc, d) => acc + (d.skill_match_percentage || 0), 0) / docs.length).toFixed(1)
      : 0;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <Card className="border-border/60 bg-card/60 backdrop-blur">
        <CardContent className="p-5 flex items-center justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Total Documents</p>
            <h3 className="text-2xl font-bold mt-1">{docs.length}</h3>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <FileText size={20} />
          </div>
        </CardContent>
      </Card>

      <Card className="border-border/60 bg-card/60 backdrop-blur">
        <CardContent className="p-5 flex items-center justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Average Match</p>
            <h3 className="text-2xl font-bold mt-1">{avgMatch}%</h3>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
            <CheckCircle2 size={20} />
          </div>
        </CardContent>
      </Card>

      <Card className="border-border/60 bg-card/60 backdrop-blur">
        <CardContent className="p-5 flex items-center justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Selected Candidates</p>
            <h3 className="text-2xl font-bold mt-1">
              {docs.filter((d) => d.status === "selected").length}
            </h3>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/10 text-blue-600">
            <Clock size={20} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
