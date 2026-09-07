import type {
  ScreeningCandidate,
  ScreeningEvaluation,
  ScreeningResult,
} from "@/shared/types";
import {
  CheckCircle2,
  XCircle,
  AlertCircle,
  Sparkles,
  BookOpen,
  Mail,
  Phone,
  Briefcase,
  GraduationCap,
  ExternalLink,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/shared/components/ui/card";
import { Badge } from "@/shared/components/ui/badge";

const statusConfig: Record<
  string,
  { label: string; variant: "default" | "destructive" | "secondary"; icon: typeof CheckCircle2 }
> = {
  selected: { label: "Strong Candidate", variant: "default", icon: CheckCircle2 },
  rejected: { label: "Not Recommended", variant: "destructive", icon: XCircle },
  pending: { label: "Under Review", variant: "secondary", icon: AlertCircle },
};

export function ScreeningResultsView({ result }: { result: ScreeningResult }) {
  const candidate: ScreeningCandidate = result.candidate || ({} as ScreeningCandidate);
  const evaluation: ScreeningEvaluation = result.evaluation || ({} as ScreeningEvaluation);
  const status = evaluation.candidate_status || "pending";
  const statusInfo = statusConfig[status.toLowerCase()] || {
    label: status,
    variant: "secondary" as const,
    icon: AlertCircle,
  };
  const StatusIcon = statusInfo.icon;
  const matchPct = evaluation.skill_match_percentage ?? 0;

  return (
    <div className="space-y-6 fade-in">
      {/* Main Candidate Card */}
      <Card className="border-border/60 bg-card/90 backdrop-blur overflow-hidden shadow-md">
        <CardHeader className="bg-muted/30 pb-4 border-b border-border/40">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <CardTitle className="text-2xl font-bold">
                {candidate.name || "Candidate Profile"}
              </CardTitle>
              <div className="flex items-center gap-4 text-xs text-muted-foreground mt-1.5 flex-wrap">
                {candidate.email && (
                  <span className="flex items-center gap-1.5">
                    <Mail size={13} className="text-primary" /> {candidate.email}
                  </span>
                )}
                {candidate.phone && (
                  <span className="flex items-center gap-1.5">
                    <Phone size={13} className="text-primary" /> {candidate.phone}
                  </span>
                )}
                {evaluation.experience_years != null && (
                  <span className="flex items-center gap-1.5">
                    <Briefcase size={13} className="text-primary" /> {evaluation.experience_years} years experience
                  </span>
                )}
              </div>
            </div>

            <Badge variant={statusInfo.variant} className="gap-1.5 px-3 py-1 text-xs font-semibold self-start sm:self-center">
              <StatusIcon size={14} /> {statusInfo.label}
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="p-6 space-y-6">
          {/* Skill Match Progress Bar */}
          <div className="p-4 rounded-xl bg-muted/40 border border-border/40">
            <div className="flex items-center justify-between text-sm font-semibold mb-2">
              <span className="flex items-center gap-2">
                <Sparkles size={16} className="text-primary" /> Overall Skill Match Score
              </span>
              <span className="text-lg font-bold text-primary">{matchPct.toFixed(1)}%</span>
            </div>
            <div className="h-3 w-full overflow-hidden rounded-full bg-muted">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  matchPct >= 75
                    ? "bg-emerald-500"
                    : matchPct >= 50
                    ? "bg-amber-500"
                    : "bg-destructive"
                }`}
                style={{ width: `${Math.min(100, Math.max(0, matchPct))}%` }}
              />
            </div>
          </div>

          {/* Skills Breakdown Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Matched Skills */}
            <div className="p-4 rounded-xl border border-emerald-500/20 bg-emerald-500/5">
              <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 mb-2 flex items-center gap-1.5">
                <CheckCircle2 size={14} /> Matched Skills ({evaluation.matched_skills?.length || 0})
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {(evaluation.matched_skills || []).map((s) => (
                  <Badge key={s} variant="default" className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs">
                    {s}
                  </Badge>
                ))}
                {!evaluation.matched_skills?.length && (
                  <span className="text-xs text-muted-foreground italic">None identified</span>
                )}
              </div>
            </div>

            {/* Missing Skills */}
            <div className="p-4 rounded-xl border border-destructive/20 bg-destructive/5">
              <h4 className="text-xs font-bold uppercase tracking-wider text-destructive mb-2 flex items-center gap-1.5">
                <XCircle size={14} /> Missing Skills ({evaluation.missing_skills?.length || 0})
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {(evaluation.missing_skills || []).map((s) => (
                  <Badge key={s} variant="destructive" className="text-xs">
                    {s}
                  </Badge>
                ))}
                {!evaluation.missing_skills?.length && (
                  <span className="text-xs text-muted-foreground italic">None missing</span>
                )}
              </div>
            </div>

            {/* Weak Skills */}
            <div className="p-4 rounded-xl border border-amber-500/20 bg-amber-500/5">
              <h4 className="text-xs font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400 mb-2 flex items-center gap-1.5">
                <AlertCircle size={14} /> Needs Strengthening ({evaluation.weak_skills?.length || 0})
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {(evaluation.weak_skills || []).map((s) => (
                  <Badge key={s} variant="secondary" className="border-amber-500/40 text-xs">
                    {s}
                  </Badge>
                ))}
                {!evaluation.weak_skills?.length && (
                  <span className="text-xs text-muted-foreground italic">None</span>
                )}
              </div>
            </div>
          </div>

          {/* Evaluation Reason */}
          {evaluation.reason && (
            <div>
              <h4 className="text-sm font-semibold mb-1.5">AI Evaluation Analysis</h4>
              <p className="text-sm text-muted-foreground leading-relaxed p-4 rounded-xl bg-muted/30 border border-border/40">
                {evaluation.reason}
              </p>
            </div>
          )}

          {/* Work History & Education */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2 border-t border-border/40">
            {candidate.work_history?.length ? (
              <div>
                <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                  <Briefcase size={16} className="text-primary" /> Work Experience
                </h4>
                <div className="space-y-2">
                  {candidate.work_history.map((w, i) => (
                    <div key={i} className="text-xs p-3 rounded-lg bg-muted/30 border border-border/40">
                      <p className="font-semibold text-foreground text-sm">{w.title || "Position"}</p>
                      <p className="text-muted-foreground">
                        {w.company || "Company"} {w.years ? `• ${w.years} yrs` : ""}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            {candidate.education?.length ? (
              <div>
                <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                  <GraduationCap size={16} className="text-primary" /> Education
                </h4>
                <div className="space-y-2">
                  {candidate.education.map((ed, i) => (
                    <div key={i} className="text-xs p-3 rounded-lg bg-muted/30 border border-border/40">
                      <p className="font-semibold text-foreground text-sm">
                        {ed.degree || "Degree"} {ed.field_of_study ? `in ${ed.field_of_study}` : ""}
                      </p>
                      <p className="text-muted-foreground">{ed.institution || "Institution"}</p>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </CardContent>
      </Card>

      {/* Recommended Learning Plan Card */}
      {result.learning_plan && result.learning_plan.resources?.length > 0 && (
        <Card className="border-primary/40 bg-gradient-to-br from-card to-primary/5 shadow-md">
          <CardHeader className="pb-3 border-b border-border/40">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BookOpen size={20} className="text-primary" />
                <CardTitle className="text-lg font-bold">Recommended Learning Plan</CardTitle>
              </div>
              {result.learning_plan.total_estimated_hours ? (
                <Badge variant="outline" className="text-xs font-semibold">
                  ~{result.learning_plan.total_estimated_hours} hours total
                </Badge>
              ) : null}
            </div>
            <CardDescription>
              Tailored learning resources to help candidate bridge skill gaps for this specific position.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {result.learning_plan.resources.map((r, i) => (
                <a
                  key={i}
                  href={r.url || "#"}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block no-underline group"
                >
                  <Card className="h-full border-border/60 hover:border-primary/50 transition-all hover:shadow-sm">
                    <CardContent className="p-4 flex flex-col justify-between h-full space-y-2">
                      <div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-primary">
                          {r.skill}
                        </span>
                        <h5 className="font-semibold text-sm group-hover:text-primary transition-colors flex items-center justify-between mt-0.5">
                          {r.title}
                          <ExternalLink size={12} className="text-muted-foreground shrink-0 ml-1" />
                        </h5>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {r.provider || "Resource"} {r.estimated_hours ? `• ~${r.estimated_hours}h` : ""}
                      </p>
                    </CardContent>
                  </Card>
                </a>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
