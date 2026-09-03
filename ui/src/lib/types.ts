// ============ Main Resume Screening app types ============
export interface HealthResponse {
  status: string;
  app: string;
  database: string;
}

export interface JobDescription {
  id: string | null;
  title: string | null;
  raw_text: string;
  min_work_experience: number | null;
  max_work_experience: number | null;
  skills: string[];
  created_at?: string | null;
}

export interface ScreeningCandidate {
  name: string | null;
  email: string | null;
  phone: string | null;
  education?: Array<{ degree?: string; field_of_study?: string; institution?: string }>;
  work_history?: Array<{ title?: string; company?: string; years?: number }>;
}

export interface ScreeningEvaluation {
  candidate_status: string;
  reason: string;
  matched_skills: string[];
  missing_skills: string[];
  weak_skills: string[];
  skill_match_percentage: number;
  experience_years: number | null;
}

export interface LearningResource {
  id?: string | null;
  skill: string;
  title: string;
  url: string;
  resource_type?: string;
  provider?: string;
  description?: string;
  estimated_hours?: number | null;
  screening_id?: string | null;
}

export interface LearningPlan {
  screening_id: string;
  candidate_name: string;
  skill_gaps: Array<{ skill: string; severity: string; reason: string }>;
  resources: LearningResource[];
  total_estimated_hours: number;
}

export interface ScreeningResult {
  candidate?: ScreeningCandidate;
  evaluation?: ScreeningEvaluation;
  learning_plan?: LearningPlan;
  model_used?: string;
}

// ============ AetherGate Gateway (provider / routing) types ============
export interface Provider {
  id: string;
  name: string;
  provider: string;
  model: string;
  api_base: string | null;
  max_tokens: number;
  temperature: number;
  is_active: boolean;
  is_validated: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProviderCreate {
  name: string;
  provider: string;
  model: string;
  api_key: string;
  api_base?: string | null;
  max_tokens?: number;
  temperature?: number;
}

export interface ProviderUpdate {
  name?: string | null;
  provider?: string | null;
  model?: string | null;
  api_key?: string | null;
  api_base?: string | null;
  max_tokens?: number | null;
  temperature?: number | null;
}

export interface ProviderValidate {
  id: string;
  success: boolean;
  message: string;
  latency_ms: number | null;
}

export interface KeyResponse {
  id: string;
  api_key: string;
}

export interface IntentRoute {
  provider: string;
  model: string;
  latency?: string;
}

export interface Intent {
  id: string;
  name: string;
  status: "healthy" | "locked" | "degraded";
  routes: IntentRoute[];
  triggers: string[];
}

export const providerPalette: Record<string, string> = {
  openai: "bg-emerald/10 text-emerald",
  anthropic: "bg-orange-500/10 text-orange-400",
  google: "bg-blue-500/10 text-blue-400",
  azure: "bg-blue-400/10 text-blue-300",
  deepseek: "bg-cyan-500/10 text-cyan-400",
  openrouter: "bg-purple-500/10 text-purple-400",
  ollama: "bg-gray-500/10 text-gray-400",
  custom: "bg-gray-500/10 text-gray-600",
};

export const providerIcon: Record<string, string> = {
  openai: "◉",
  anthropic: "◈",
  google: "◆",
  azure: "◆",
  deepseek: "◎",
  openrouter: "◇",
  ollama: "⬡",
  custom: "⬡",
};
