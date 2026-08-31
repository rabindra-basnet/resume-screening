# Agentic Resume Screening & Matching

A scalable, agentic resume-screening and candidate-matching application. It parses
candidate resumes (PDF), extracts structured profiles, screens them against job
descriptions, and produces an evaluation verdict — all through an **LLM-agent
pipeline that supports any OpenAI-compatible provider** (OpenAI, Anthropic, local
vLLM/Ollama, etc.).

> Status: backend foundation complete (API, agents with multi-provider LLM
> abstraction, PostgreSQL/SQLite persistence, tests, security linting).
> A React (Next.js SSR) frontend is the next step.

## Architecture

Modular monolith with clean layer boundaries, deployable as a single serverless
function on Vercel (Fluid Compute).

```
Client (React/Next.js SSR - planned)
        │
        ▼
FastAPI  /api/v1  (versioned REST API)
        ▼
ScreeningService ────► AgentOrchestrator
- PDF parsing              ├─ ResumeExtractorAgent
- JD resolution/caching    ├─ JDGeneratorAgent
- result persistence       └─ EvaluatorAgent
        │                           │
   Database                      LiteLLM (multi-provider)
Postgres/Neon ↔ SQLite          OpenAI / Anthropic / local
```

### Layer map

| Layer | Path | Responsibility |
|-------|------|----------------|
| API | `api/`, `app/api/v1/` | Versioned HTTP endpoints, request validation, dependency injection |
| Services | `app/services/` | Business logic orchestration (screening workflow) |
| Agents | `app/agents/` | LLM pipeline: extract, generate JD, evaluate |
| Tools | `app/tools/` | Non-LLM helpers (PDF parsing, skill matching) |
| Models | `app/models/` | Pydantic contracts shared across layers |
| Database | `app/database/` | Async SQLAlchemy engine, schema, repositories |
| Config | `app/config/` | Pydantic settings + constants |

## Tech stack

- **Backend:** FastAPI, Uvicorn (ASGI)
- **LLM orchestration:** LiteLLM (OpenAI-compatible, multi-provider, retries)
- **Data:** SQLAlchemy 2.0 (async) + Alembic migrations
  - Dev: SQLite — Prod: Neon PostgreSQL (free tier, scale-to-zero)
- **PDF:** pdfplumber
- **Validation:** Pydantic v2
- **Quality/security:** ruff (incl. security rules), bandit, mypy, pytest, pre-commit
- **Deploy target:** Vercel Fluid Compute (`api/index.py`, `vercel.json`)

## Getting started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (package/project manager)
- An OpenAI-compatible API key

### 1. Install & configure

```bash
uv sync
cp .env.example .env          # then fill in LLM_API_KEY and DATABASE_URL
```

### 2. Configure the LLM provider

Edit `.env`. Swapping providers is an env-var change (see `.env.example`):

```bash
# OpenAI
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=sk-...

# Anthropic
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-20250514
LLM_API_KEY=sk-ant-...

# Local / OpenAI-compatible (vLLM, Ollama, ...)
LLM_PROVIDER=openai
LLM_MODEL=llama3.1
LLM_API_KEY=dummy
LLM_API_BASE=http://localhost:11434/v1
```

### 3. Run the API

```bash
uv run resume-screen           # or: uv run uvicorn app.main:app --reload
```

Interactive docs: http://localhost:8000/docs

### 4. Screen a resume

```bash
curl -X POST http://localhost:8000/api/v1/screening \
  -F "resume=@path/to/resume.pdf" \
  -F "job_description=Senior Python Engineer requires Python and FastAPI."
```

You can also pre-register a job description and reference it by id:

```bash
curl -X POST http://localhost:8000/api/v1/job-descriptions \
  -H "Content-Type: application/json" \
  -d '{"title": "Senior Python Engineer", "raw_text": "Requires Python and FastAPI."}'
```

## Provider-agnostic LLM configuration

All agents route through a single `LLMClient` wrapper around LiteLLM
(`app/agents/llm_client.py`) configured by `app/config/settings.py`. This gives:

- One interface across OpenAI, Anthropic, Azure, Google, local endpoints
- Built-in retry with budget and timeout controls
- No vendor lock-in — switch providers without code changes

## Database

| Environment | URL | Notes |
|-------------|-----|-------|
| Development | `sqlite:///./screening.db` | Default, zero config |
| Production | `postgresql+asyncpg://...` (Neon) | Free tier, autoscaling |

Schema is defined in `app/database/schema.py`; use Alembic for migrations
(`alembic revision --autogenerate`).

## Code hardening (code review + security reviewer)

Quality and security gates run locally and in CI (`.github/workflows/ci.yml`):

| Gate | Tool | What it catches |
|------|------|-----------------|
| Lint + docstrings | ruff (`D`, `S`, `B`, `BLE`, ...) | Style, missing docstrings, security smells |
| Security scan | bandit | Injection, SSRF, hardcoded secrets, weak crypto |
| Type checking | mypy | Type errors across the app |
| Tests | pytest | Unit + integration coverage |
| Pre-commit | `uv run pre-commit install` | Runs all the above on every commit |

Run them locally:

```bash
uv run ruff check app api tests
uv run bandit -c pyproject.toml -r app -ll
uv run mypy app
uv run pytest
```

## Deployment (Vercel Fluid Compute)

- Entry point: `api/index.py` exports the ASGI `app`
- Config: `vercel.json` sets `fluid: true`, 300s max duration, 1GB memory
- Serverless-aware design: cached config singleton, minimal top-level imports,
  conservative DB pooling, in-process JD caching to avoid repeat LLM cost.

```bash
uv run vercel        # or deploy via the Vercel dashboard / GitHub integration
```

## Roadmap

- [x] Modular backend with provider-agnostic LLM agents
- [x] Persistence (SQLite dev / Neon Postgres prod), result + JD repositories
- [x] Versioned API, structured output, retries, code-hardening gates
- [ ] React (Next.js SSR) frontend mounted to the FastAPI API
- [ ] Auth (API keys → OAuth) for public access
- [ ] Batch/parallel resume screening

## License

MIT
