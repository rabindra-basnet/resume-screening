import type { FullReviewResult } from "@/shared/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Badge } from "@/shared/components/ui/badge";
import {
  AlertTriangle,
  Target,
  PenTool,
  Mic,
  CheckCircle2,
  ArrowRight,
  Star,
} from "lucide-react";

function Bullet({ label, items }: { label: string; items: string[] }) {
  if (!items || items.length === 0) return null;
  return (
    <div>
      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
        {label}
      </p>
      <ul className="space-y-1.5">
        {items.map((item, i) => (
          <li key={i} className="flex gap-2 text-sm text-foreground/90">
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary/60" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Section({
  icon,
  title,
  accent,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  accent: string;
  children: React.ReactNode;
}) {
  return (
    <Card className="border-border/60 bg-card/80 backdrop-blur shadow-sm">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${accent}`}>
            {icon}
          </div>
          <CardTitle className="text-base">{title}</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="text-sm space-y-4">{children}</CardContent>
    </Card>
  );
}

export function CvReviewResults({
  results,
}: {
  results: FullReviewResult;
}) {
  const hasAny =
    results.brutal_review ||
    results.ats_optimization ||
    results.bullet_points ||
    results.industry_tone ||
    results.final_polish;

  if (!hasAny) {
    return <p className="text-sm text-muted-foreground">No review results yet.</p>;
  }

  return (
    <div className="space-y-4">
      {results.brutal_review && (
        <Section
          icon={<AlertTriangle size={16} />}
          title="Brutal Honest Review"
          accent="bg-destructive/10 text-destructive"
        >
          <Bullet label="Weak Areas" items={results.brutal_review.weak_areas} />
          <Bullet label="Missing Elements" items={results.brutal_review.missing_elements} />
          <Bullet label="Immediate Rejections" items={results.brutal_review.immediate_rejections} />
          <Bullet label="Strengths" items={results.brutal_review.strengths} />
          <Bullet label="Actionable Fixes" items={results.brutal_review.actionable_fixes} />
          {results.brutal_review.overall_assessment && (
            <p className="rounded-xl bg-muted/50 p-3 text-sm">
              {results.brutal_review.overall_assessment}
            </p>
          )}
        </Section>
      )}

      {results.ats_optimization && (
        <Section
          icon={<Target size={16} />}
          title="ATS Optimization"
          accent="bg-primary/10 text-primary"
        >
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              ATS Score Estimate
            </p>
            <Badge variant="secondary" className="text-sm font-bold">
              {Math.round(results.ats_optimization.ats_score_estimate)}%
            </Badge>
          </div>
          <Bullet label="Missing Keywords" items={results.ats_optimization.missing_keywords} />
          <Bullet label="Skills to Highlight" items={results.ats_optimization.skills_to_highlight} />
          {results.ats_optimization.bullet_restructurings.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                Bullet Restructuring
              </p>
              <ul className="space-y-3">
                {results.ats_optimization.bullet_restructurings.map((b, i) => (
                  <li key={i} className="rounded-xl border border-border/60 p-3 space-y-1.5">
                    <p className="text-xs text-muted-foreground line-through">{b.original}</p>
                    <p className="flex items-center gap-1.5 text-sm font-medium">
                      <ArrowRight size={14} className="text-primary shrink-0" /> {b.suggested}
                    </p>
                    <p className="text-xs text-muted-foreground">{b.reason}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {results.ats_optimization.summary && (
            <p className="rounded-xl bg-muted/50 p-3 text-sm">{results.ats_optimization.summary}</p>
          )}
        </Section>
      )}

      {results.bullet_points && (
        <Section
          icon={<PenTool size={16} />}
          title="Bullet Point Transformer"
          accent="bg-amber-500/10 text-amber-600"
        >
          {results.bullet_points.transformed_bullets.map((b, i) => (
            <div key={i} className="rounded-xl border border-border/60 p-3 space-y-1">
              <p className="text-xs text-muted-foreground">{b.original}</p>
              <p className="text-sm font-medium text-foreground">
                <span className="text-primary font-bold">{b.action_verb} </span>
                {b.task}
                {b.result ? ` — ${b.result}` : ""}
              </p>
            </div>
          ))}
          <Bullet label="Questions for You" items={results.bullet_points.questions_for_user} />
        </Section>
      )}

      {results.industry_tone && (
        <Section
          icon={<Mic size={16} />}
          title="Industry Tone Match"
          accent="bg-emerald-500/10 text-emerald-600"
        >
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              Alignment Score
            </p>
            <Badge variant="secondary" className="text-sm font-bold">
              {Math.round(results.industry_tone.industry_alignment_score)}%
            </Badge>
          </div>
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">
              Rewritten Summary
            </p>
            <p className="rounded-xl bg-muted/50 p-3 text-sm">
              {results.industry_tone.rewritten_summary}
            </p>
          </div>
          {results.industry_tone.rewritten_skills.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                Rewritten Skills
              </p>
              <div className="flex flex-wrap gap-1.5">
                {results.industry_tone.rewritten_skills.map((s, i) => (
                  <Badge key={i} variant="secondary">{s}</Badge>
                ))}
              </div>
            </div>
          )}
          {results.industry_tone.tone_analysis && (
            <p className="text-sm text-muted-foreground">{results.industry_tone.tone_analysis}</p>
          )}
        </Section>
      )}

      {results.final_polish && (
        <Section
          icon={<Star size={16} />}
          title="Final Polish"
          accent="bg-violet-500/10 text-violet-600"
        >
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              Quality Score
            </p>
            <Badge variant="secondary" className="text-sm font-bold">
              {Math.round(results.final_polish.overall_quality_score)}%
            </Badge>
          </div>
          {results.final_polish.tense_issues.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                Tense Issues
              </p>
              <ul className="space-y-1.5">
                {results.final_polish.tense_issues.map((t, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm">
                    <span className="text-muted-foreground line-through">{t.original}</span>
                    <ArrowRight size={14} className="text-primary shrink-0" />
                    <span className="font-medium">{t.fixed}</span>
                    <span className="ml-auto text-xs text-muted-foreground">{t.section}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {results.final_polish.cliche_replacements.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                Cliche Replacements
              </p>
              <ul className="space-y-1.5">
                {results.final_polish.cliche_replacements.map((c, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm">
                    <span className="text-muted-foreground line-through">{c.original}</span>
                    <ArrowRight size={14} className="text-primary shrink-0" />
                    <span className="font-medium">{c.replacement}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <Bullet
            label="Generic to Specific"
            items={results.final_polish.generic_to_specific.map((g) => `${g.original} → ${g.improved}`)}
          />
          {results.final_polish.final_summary && (
            <p className="flex items-start gap-2 rounded-xl bg-emerald-500/5 border border-emerald-500/20 p-3 text-sm">
              <CheckCircle2 size={16} className="text-emerald-500 mt-0.5 shrink-0" />
              <span>{results.final_polish.final_summary}</span>
            </p>
          )}
        </Section>
      )}
    </div>
  );
}
