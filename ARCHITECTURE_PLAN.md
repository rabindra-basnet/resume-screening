# Agentic Resume Screening — Scalable Architecture Plan

## Current State Assessment

Your codebase has **3 files that matter** (main.py, parsepdf.py, prompts.py), **3 agent files**, a **Streamlit UI**, and **~240 lines of code**. It's a linear pipeline: PDF → Extract Resume → Extract JD → Evaluate. No database, no tests, no error handling, no type safety, no `.gitignore`.

**What works:** The core concept is sound — 3 sequential LLM calls producing structured evaluation.

**What breaks at scale:** No provider abstraction, hardcoded JD path, no caching (re-extracts same JD every request), inconsistent error handling, no persistence, no auth.

---

## Constraints Driving Every Decision

| Constraint | Implication |
|---|---|
| **Vercel Fluid Compute** | Stateless functions, 300s Hobby / 800s Pro timeout, Python cold starts 300-800ms, no persistent processes, bundle ≤500MB, `/tmp` only writable fs |
| **Budget < $50/mo** | Free-tier DB (Neon/Supabase), no Redis, minimize LLM calls via caching, Vercel free/Hobby tier |
| **Multiple LLM providers** | LiteLLM abstraction layer, not raw OpenAI SDK |
| **Start internal → go public** | Auth from day 1 (simple), API versioning, modular design |
| **Growing team (5-15)** | Modular monolith, not microservices. Clean module boundaries for team ownership later |
| **Every function/class needs docstrings** | Enforced via linting (ruff D-style rules) |

---

## 1. Proposed Folder Structure

```
agentic-resume-screening/
├── api/                              # Vercel serverless entry point
│   └── index.py                      # FastAPI app mounted for Vercel
│
├── app/                              # Core application package
│   ├── __init__.py
│   │
│   ├── main.py                       # FastAPI app factory, middleware, lifespan
│   │
│   ├── config/                       # Configuration & environment
│   │   ├── __init__.py
│   │   ├── settings.py               # Pydantic BaseSettings (env vars, LLM config)
│   │   └── constants.py              # App-wide constants (limits, defaults)
│   │
│   ├── models/                       # Pydantic data models (shared contracts)
│   │   ├── __init__.py
│   │   ├── candidate.py              # CandidateProfile, Education, WorkExperience
│   │   ├── job_description.py        # JobDescription, JDSkills
│   │   ├── evaluation.py             # EvaluationResult, SkillMatch
│   │   └── api.py                    # Request/Response models for API endpoints
│   │
│   ├── database/                     # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py             # Engine/session factory (SQLite dev, Neon prod)
│   │   ├── schema.py                 # SQLAlchemy Table definitions
│   │   └── repositories/             # Data access layer
│   │       ├── __init__.py
│   │       ├── resume_repository.py  # CRUD for screening results
│   │       └── jd_repository.py      # CRUD for job descriptions
│   │
│   ├── agents/                       # LLM agent orchestration
│   │   ├── __init__.py
│   │   ├── base.py                   # BaseAgent ABC (provider abstraction)
│   │   ├── resume_extractor.py       # Extract candidate profile from resume text
│   │   ├── jd_extractor.py           # Extract structured JD from text
│   │   ├── evaluator.py              # Score candidate against JD
│   │   └── orchestrator.py           # Pipeline runner (sequential + future parallel)
│   │
│   ├── tools/                        # Agent tooling (PDF parsing, matching, etc.)
│   │   ├── __init__.py
│   │   ├── pdf_parser.py             # PDF text extraction (replaces parsepdf.py)
│   │   ├── skill_matcher.py          # Skill matching logic (fuzzy + semantic)
│   │   └── text_preprocessor.py      # Resume/JD text cleaning
│   │
│   ├── prompts/                      # Prompt templates
│   │   ├── __init__.py
│   │   ├── resume_extraction.py      # Resume extraction prompt
│   │   ├── jd_extraction.py          # JD extraction prompt
│   │   └── evaluation.py             # Evaluation prompt
│   │
│   ├── services/                     # Business logic layer
│   │   ├── __init__.py
│   │   ├── screening_service.py      # Orchestrates full screening workflow
│   │   └── cache_service.py          # In-memory / module-level JD cache
│   │
│   └── api/                          # API route definitions
│       ├── __init__.py
│       ├── v1/                       # Versioned API
│       │   ├── __init__.py
│       │   ├── screening.py          # POST /api/v1/screening
│       │   ├── job_descriptions.py   # CRUD for JDs
│       │   └── health.py             # GET /api/v1/health
│       └── deps.py                   # Dependency injection (DB sessions, auth)
│
├── frontend/                          # Frontend (React / Next.js SSR, mounted to FastAPI)
│   └── app/                           # Next.js App Router — server-rendered, calls /api/v1
│
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_agents.py
│   │   ├── test_pdf_parser.py
│   │   └── test_models.py
│   └── integration/
│       ├── test_screening_flow.py
│       └── test_api.py
│
├── resources/                        # Static resources
│   └── job_description.pdf
│
├── migrations/                       # Database migrations (Alembic)
│   └── ...
│
├── .gitignore
├── .env.example                      # Documented env template (no secrets)
├── pyproject.toml                    # Project config, deps, ruff, pytest
├── vercel.json                       # Vercel deployment config
├── requirements.txt                  # Production dependencies (pinned)
└── README.md
```

### Why this structure?

| Decision | Rationale |
|---|---|
| `api/index.py` as Vercel entry point | Vercel auto-detects FastAPI in `api/index.py`. Keeps Vercel config separate from app logic |
| `app/` as core package | Clean separation — app logic is deployable to Vercel, Railway, or anywhere |
| `config/` with Pydantic Settings | Type-safe env vars, validation at startup, supports `OPENAI_API_BASE` for provider switching |
| `models/` with Pydantic | Shared contracts between API, agents, and database. Enforced at every boundary |
| `database/` with SQLAlchemy | ORM for schema management, works with SQLite (dev) and PostgreSQL (prod). Migration-ready |
| `agents/base.py` | ABC defining the agent contract — all agents implement `extract()` or `evaluate()` |
| `tools/` for non-LLM logic | PDF parsing, skill matching — things agents call but aren't LLM calls themselves |
| `services/` for orchestration | Business logic that wires agents + DB + cache together |
| `api/v1/` versioning | From day 1, so going public doesn't break existing consumers |

---

## 2. Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                            │
│  POST /api/v1/screening     POST /api/v1/job-descriptions  │
│  GET  /api/v1/health        GET  /api/v1/results/{id}      │
└──────────────┬──────────────────────────┬───────────────────┘
               │                          │
       ┌───────▼────────┐        ┌────────▼─────────┐
       │ ScreeningService│        │  JD Repository   │
       │   (orchestrate) │        │  (CRUD + cache)  │
       └───────┬────────┘        └──────────────────┘
               │
    ┌──────────▼──────────────────────────┐
    │        Agent Orchestrator            │
    │  (sequential pipeline with retry)    │
    └──┬────────────┬──────────────┬──────┘
       │            │              │
  ┌────▼────┐ ┌────▼────┐  ┌─────▼─────┐
  │ Resume  │ │   JD    │  │ Candidate │
  │Extract  │ │Extract  │  │ Evaluator │
  │ Agent   │ │ Agent   │  │   Agent   │
  └────┬────┘ └────┬────┘  └─────┬─────┘
       │            │              │
  ┌────▼────────────▼──────────────▼─────┐
  │     LiteLLM Provider Abstraction     │
  │  (OpenAI / Anthropic / Local / etc.) │
  └──────────────────────────────────────┘
               │
  ┌────────────▼──────────────────────┐
  │        Database Layer             │
  │  SQLite (dev) / Neon PostgreSQL   │
  │  - screening_results              │
  │  - job_descriptions               │
  │  - candidates                     │
  └───────────────────────────────────┘
```

### Request Flow (detailed)

```
1. Client uploads resume PDF + jd_id (or inline JD text)
         │
2. ScreeningService.validate_input()
   - Check file type, size (max 10MB)
   - If jd_id provided, load from DB
         │
3. PDFParser.extract_text(pdf_bytes)
   - PyPDF2 / pdfplumber extraction
   - Return clean text
         │
4. JD loaded from cache or DB (no re-extraction!)
         │
5. AgentOrchestrator.run([
      ResumeExtractor(text),     → CandidateProfile (Pydantic)
      Evaluator(profile, jd),    → EvaluationResult (Pydantic)
   ])
   - Sequential execution with retry (3 attempts, exponential backoff)
   - Each step validated against Pydantic model
   - Timeout: 60s per LLM call
         │
6. ScreeningService.save_result()
   - Persist to DB
   - Return EvaluationResult
         │
7. API returns structured JSON response
```

---

## 3. Database Choice: SQLite (dev) → Neon PostgreSQL (prod)

### Why this combo fits the <$50/mo budget:

| Factor | Decision |
|---|---|
| **Dev** | SQLite — zero cost, zero config, file-based |
| **Prod** | **Neon PostgreSQL** free tier — 0.5 GB storage, autoscale to zero, perfect for resume data |
| **ORM** | SQLAlchemy 2.0 — async support, works with both SQLite and PostgreSQL |
| **Migrations** | Alembic — schema versioning from day 1 |
| **Why not MongoDB** | Your data is relational (candidates ↔ evaluations ↔ job_descriptions). SQL fits naturally |
| **Why not Turso** | SQLite-based, good but less ecosystem than PostgreSQL |
| **Why not Supabase** | Also viable, but Neon's scale-to-zero is better for <$50 budget |

### Schema Design

```sql
-- job_descriptions
CREATE TABLE job_descriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    extracted_skills JSONB,          -- ["Python", "SQL", "FastAPI"]
    min_experience_years INTEGER,
    max_experience_years INTEGER,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- screening_results
CREATE TABLE screening_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jd_id UUID REFERENCES job_descriptions(id),
    resume_filename TEXT,
    resume_text TEXT,                -- extracted text
    candidate_name TEXT,
    candidate_email TEXT,
    candidate_profile JSONB,         -- full extracted profile
    evaluation JSONB,                -- {status, reason, skill_match_pct}
    status TEXT CHECK (status IN ('selected', 'rejected', 'pending')),
    skill_match_percentage DECIMAL(5,2),
    llm_model_used TEXT,             -- track which provider was used
    llm_cost_usd DECIMAL(10,6),      -- track cost per screening
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- jd_cache (for LLM extraction caching)
CREATE TABLE jd_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text_hash TEXT UNIQUE NOT NULL,  -- SHA256 of raw JD text
    extracted_data JSONB NOT NULL,
    model_used TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 4. LLM Provider Abstraction: LiteLLM

### Why LiteLLM?

| Factor | LiteLLM | Raw OpenAI SDK |
|---|---|---|
| Multi-provider support | OpenAI, Anthropic, Google, Azure, local, 100+ | OpenAI only |
| Cost | Free, open source | Free |
| OpenAI-compatible API | Yes — unified interface | N/A |
| Fallback/retry | Built-in | Manual |
| Model switching | Change one string | Code changes |

### Configuration Model

```python
# app/config/settings.py — the key piece
class LLMProviderConfig(BaseSettings):
    """LLM provider configuration supporting multiple backends."""

    # Primary provider
    llm_provider: str = "openai"           # openai, anthropic, azure, custom
    llm_model: str = "gpt-4o-mini"         # model name
    llm_api_key: str = ""                  # provider API key
    llm_api_base: str | None = None        # custom endpoint (for local/proxy)

    # Fallback provider
    llm_fallback_provider: str | None = None
    llm_fallback_model: str | None = None
    llm_fallback_api_key: str | None = None
    llm_fallback_api_base: str | None = None

    # Budget controls
    llm_max_tokens: int = 2000
    llm_temperature: float = 0.1           # low for structured extraction
    llm_timeout_seconds: int = 60
    llm_max_retries: int = 3
```

### Switching providers = env var change only:

```bash
# OpenAI
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=sk-...

# Anthropic
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-20250514
LLM_API_KEY=sk-ant-...

# Local (Ollama/vLLM)
LLM_PROVIDER=openai           # use OpenAI-compatible endpoint
LLM_MODEL=llama3.1
LLM_API_KEY=dummy
LLM_API_BASE=http://localhost:11434/v1
```

---

## 5. Agent Design Pattern

Every agent follows the same contract:

```python
class BaseAgent(ABC):
    """Abstract base class for all LLM agents."""

    @abstractmethod
    async def run(self, input_data: str, **kwargs) -> BaseModel:
        """Execute the agent's task and return structured output."""

    def _build_messages(self, input_data: str, **kwargs) -> list[dict]:
        """Construct the message list for the LLM call."""

    def _parse_response(self, raw: str, model: type[BaseModel]) -> BaseModel:
        """Parse LLM JSON response into a Pydantic model with validation."""
```

Each agent returns a **Pydantic model**, not a raw string. This enforces structured output at the type level.

---

## 6. Vercel Fluid Compute Deployment Strategy

### `vercel.json` configuration:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "fluid": true,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "api/index.py" }
  ],
  "functions": {
    "api/index.py": {
      "maxDuration": 300,
      "memory": 1024
    }
  }
}
```

### Resource consumption considerations:

| Concern | Strategy |
|---|---|
| **Cold starts** | Minimize imports at module level; use `@lru_cache` for one-time init |
| **3 LLM calls per request** | Each ~10-30s, total ~60-90s — well within 300s limit |
| **No persistent state** | DB for persistence, module-level `lru_cache` for JD extraction cache |
| **File uploads** | Stream to `/tmp`, parse, delete immediately |
| **Bundle size** | Pin dependencies, avoid heavy ML libs (no torch/sklearn) |
| **Concurrent requests** | Module-level DB pool shared safely (SQLAlchemy async) |
| **Background tasks** | Use Vercel Cron Jobs for any batch processing |

---

## 7. Cost Estimate (<$50/mo)

| Service | Tier | Cost |
|---|---|---|
| Vercel | Hobby (Fluid Compute) | $0 (or $20 Pro) |
| Neon PostgreSQL | Free tier (0.5 GB) | $0 |
| LLM API (gpt-4o-mini) | ~1000 screens/mo × 2 calls × ~$0.001 | ~$2/mo |
| LLM API (Claude Sonnet fallback) | minimal usage | ~$1/mo |
| Domain (if needed) | — | ~$1/mo |
| **Total** | | **~$3-25/mo** |

---

## 8. Implementation Phases

### Phase 1: Foundation (Estimated: 1-2 days)
- [ ] Add `.gitignore`, fix `.env` handling
- [ ] Create `pyproject.toml` with pinned deps + ruff config
- [ ] Create `app/config/settings.py` with Pydantic BaseSettings
- [ ] Create all Pydantic models (`app/models/`)
- [ ] Add docstrings to every existing function/class
- [ ] Restructure folder layout per diagram above

### Phase 2: Provider Abstraction (Estimated: 1 day)
- [ ] Install and configure LiteLLM
- [ ] Create `app/agents/base.py` with BaseAgent ABC
- [ ] Refactor 3 existing agents to use base class + LiteLLM
- [ ] Add structured output parsing with Pydantic validation
- [ ] Add retry/timeout logic

### Phase 3: Database Layer (Estimated: 1 day)
- [ ] Set up SQLAlchemy 2.0 + Alembic
- [ ] Create schema (job_descriptions, screening_results, jd_cache)
- [ ] Create repository classes
- [ ] SQLite for dev, Neon connection string for prod
- [ ] Implement JD caching (avoid re-extraction)

### Phase 4: API & Services (Estimated: 1-2 days)
- [ ] Create `ScreeningService` orchestration layer
- [ ] Create versioned API routes (`/api/v1/`)
- [ ] Add proper error handling (custom exceptions, HTTP error responses)
- [ ] Add request/response validation (Pydantic)
- [ ] Add health check endpoint
- [ ] Replace `print()` with `logging` module

### Phase 5: Vercel Deployment (Estimated: 0.5 day)
- [ ] Create `api/index.py` Vercel entry point
- [ ] Create `vercel.json` configuration
- [ ] Test deployment
- [ ] Set environment variables in Vercel dashboard

### Phase 6: Quality & Testing (Estimated: 1 day)
- [ ] Write unit tests for agents, models, PDF parser
- [ ] Write integration test for full screening flow
- [ ] Add ruff linting with D-style docstring enforcement
- [ ] Add pre-commit hooks

### Phase 7: Frontend & Auth (Future)
- [ ] Auth layer (API keys for internal, OAuth for public)
- [ ] Improve/migrate UI to **Next.js (React) SSR frontend** mounted to the FastAPI API
- [ ] Batch screening (upload multiple resumes)
- [ ] Dashboard for screening history

---

## 9. Docstring Convention (enforced via ruff)

Every module, class, function, and method gets a docstring:

```python
"""PDF text extraction utilities.

Provides functions to extract text content from PDF files
using pdfplumber for accurate text and table extraction.
"""

class ResumeExtractor(BaseAgent):
    """Extract structured candidate profiles from resume text.

    Uses an LLM to parse unstructured resume text into a structured
    CandidateProfile model with education, experience, and skills.
    """

    async def run(self, resume_text: str, **kwargs) -> CandidateProfile:
        """Extract candidate profile from resume text.

        Args:
            resume_text: Raw text content extracted from the resume PDF.
            **kwargs: Additional parameters (model override, temperature).

        Returns:
            CandidateProfile with extracted structured data.

        Raises:
            ExtractionError: If LLM fails to produce valid structured output.
            TimeoutError: If LLM call exceeds configured timeout.
        """
```

---

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Python cold start on Vercel (300-800ms) | First request slow | Module-level `lru_cache` for config; minimal top-level imports |
| LLM API rate limits | Screening failures | LiteLLM fallback providers; retry with exponential backoff |
| Vercel 300s timeout (Hobby) | Long screenings timeout | Profile optimization; use gpt-4o-mini (fast) as default |
| Neon free tier 0.5 GB limit | Data growth | Monitor usage; upgrade to $19/mo plan (still under budget) |
| LLM cost spike | Budget overrun | Track `llm_cost_usd` per screening; set monthly alerts |
| Concurrent requests + shared state | Race conditions | Module-level singletons are read-only; DB handles writes safely |

---

This plan keeps you well under $50/mo, supports all LLM providers via a single config change, deploys cleanly to Vercel Fluid Compute, and sets you up for the internal → public transition.
