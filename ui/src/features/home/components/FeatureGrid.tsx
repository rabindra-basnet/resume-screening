import {
  Briefcase,
  Upload,
  Sparkles,
  BrainCircuit,
  TrendingUp,
  GraduationCap,
} from "lucide-react";
import { Card, CardContent } from "@/shared/components/ui/card";

const steps = [
  {
    n: "01",
    title: "Job Requirements",
    desc: "Paste job requirements or select from saved Job Descriptions to extract core skills.",
    icon: Briefcase,
  },
  {
    n: "02",
    title: "Upload Candidate Resume",
    desc: "Upload PDF or DOCX resume. The AI parser extracts work history, education, and skills.",
    icon: Upload,
  },
  {
    n: "03",
    title: "Instant AI Match Score",
    desc: "Get candidate match percentage, identified skill gaps, and automated learning plan.",
    icon: Sparkles,
  },
];

const features = [
  {
    icon: BrainCircuit,
    title: "AI Candidate Evaluation",
    desc: "Detailed qualitative matching that analyzes context, recency, and depth of technical skills—not simple keyword counting.",
  },
  {
    icon: TrendingUp,
    title: "Precision Gap Analysis",
    desc: "Identifies exact missing or weak technical competencies so hiring managers know precisely what questions to probe in technical interviews.",
  },
  {
    icon: GraduationCap,
    title: "Automated Learning Center",
    desc: "Generates tailored learning resources and estimated study hours so candidates or team members can rapidly close skill gaps.",
  },
];

export function FeatureGrid() {
  return (
    <div className="space-y-16">
      {/* How it works */}
      <section className="space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900">Streamlined 3-Step Candidate Screening</h2>
          <p className="text-slate-600 text-base">
            From company Job Description (JD) to detailed candidate match report in seconds.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          {steps.map((s) => {
            const Icon = s.icon;
            return (
              <Card key={s.n} className="relative overflow-hidden border-slate-200/80 bg-white/90 shadow-sm transition-all hover:border-blue-300 hover:shadow-md">
                <CardContent className="p-7 space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-2xl font-black text-blue-600/30">{s.n}</span>
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
                      <Icon size={20} />
                    </div>
                  </div>
                  <h3 className="text-lg font-bold text-slate-900">{s.title}</h3>
                  <p className="text-sm text-slate-600 leading-relaxed">{s.desc}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      {/* What you get back */}
      <section className="space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900">Built for Modern Hiring Teams & Candidates</h2>
          <p className="text-slate-600 text-base">
            Go beyond simple keyword matching with deep semantic evaluation and actionable insights.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          {features.map((f) => {
            const Icon = f.icon;
            return (
              <Card key={f.title} className="border-slate-200/80 bg-white/90 shadow-sm transition-all hover:border-blue-300 hover:shadow-md">
                <CardContent className="p-7 space-y-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
                    <Icon size={24} />
                  </div>
                  <h3 className="text-lg font-bold text-slate-900">{f.title}</h3>
                  <p className="text-sm text-slate-600 leading-relaxed">{f.desc}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>
    </div>
  );
}
