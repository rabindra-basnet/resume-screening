# Agentic Resume Screening & Matching

A scalable, agentic resume-screening and candidate-matching application. It parses
candidate resumes (PDF/DOCX), extracts structured profiles, screens them against job
descriptions, and produces an evaluation verdict — all through an **LLM-agent
pipeline that supports any OpenAI-compatible provider** (OpenAI, Anthropic, local
vLLM/Ollama, etc.).

Live at **https://ats.saastralabs.com**.

## Architecture

Modular monolith with clean layer boundaries, deployed as a single serverless
function on Vercel (Fluid Compute) with a React (Vite) SPA frontend.

```
Client (React/Vite SPA, served by Vercel)
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
| Frontend | `ui/` | React (Vite + TypeScript + Tailwind) SPA |

## Tech stack

- **Backend:** FastAPI, Uvicorn (ASGI)
- **Frontend:** React 18, Vite, TypeScript, Tailwind CSS, React Router
- **Auth:** Google OAuth (authlib) + server-side `sessions` table storing the validated Google JWT; the browser only gets an opaque session-id cookie
- **LLM orchestration:** LiteLLM (OpenAI-compatible, multi-provider, retries)
- **Data:** SQLAlchemy 2.0 (async) + Alembic migrations
  - Dev: SQLite — Prod: Neon PostgreSQL (free tier, scale-to-zero)
- **PDF:** pdfplumber
- **Observability:** Vercel Web Analytics + Speed Insights
- **Security:** Vercel BotID (bot protection, configured in the dashboard)
- **Validation:** Pydantic v2
- **Quality/security:** ruff (incl. security rules), bandit, mypy, pytest, pre-commit
- **Deploy target:** Vercel Fluid Compute (`api/index.py`, `vercel.json`)

## Getting started

### Prerequisites

- Python 3.12+ and Node 20+
- [uv](https://docs.astral.sh/uv/) (Python package/project manager)
- An OpenAI-compatible API key
- A Google OAuth client (for login)

### 1. Backend install & configure

```bash
uv sync
cp .env.example .env          # then fill in the variables below
```

Key environment variables:

| Variable | Purpose |
|----------|---------|
| `APP_ENV` | `development` or `production` |
| `APP_ORIGIN` | Public origin, e.g. `http://localhost:8000` or `https://ats.saastralabs.com` |
| `SESSION_SECRET` | Secret used to sign the OAuth `state` cookie (required in production) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth credentials |
| `DATABASE_URL` | Neon Postgres (prod) or SQLite (dev) |
| `LLM_PROVIDER` / `LLM_MODEL` / `LLM_API_KEY` | LLM routing (see below) |

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

### 3. Set up Google OAuth

1. Create a project in [Google Cloud Console](https://console.cloud.google.com),
   enable the **Google+ / OAuth** API, and create OAuth **Web** client credentials.
2. Add the authorized redirect URI:
   `https://ats.saastralabs.com/api/v1/auth/callback/google`
   (use `http://localhost:8000/api/v1/auth/callback/google` for local dev).
3. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env` / your
   environment.

### 4. Run the full application (Backend + Frontend)

Using **Honcho** (installed automatically via `uv`):

```bash
uv run honcho start
```

This starts both the **FastAPI backend** (`http://localhost:8000`) and the **Vite React UI** (`http://localhost:5173`) in a single terminal with colored output.

Alternatively, run them separately:

```bash
# Terminal 1: FastAPI Backend
uv run uvicorn app.main:app --reload

# Terminal 2: Vite React UI
cd ui && npm run dev
```

## Auth flow (Google OAuth)

1. User clicks **Sign in with Google** → `GET /api/v1/auth/login/google` redirects
   to Google with a CSRF `state` token stored in the session cookie.
2. Google redirects back to `/api/v1/auth/callback/google?code=...&state=...`.
3. The callback exchanges the code for tokens, validates the Google JWT (`id_token`)
   and the CSRF `state`, creates/updates the user, and inserts a row into the
   `sessions` table bound to that Google JWT. The browser only receives an opaque
   session id in the `aether_session` cookie — the JWT never leaves the server.
4. The browser is redirected to `/account`. Subsequent requests authenticate by
   looking the session cookie up in the DB (`GET /api/v1/auth/me`); expired or
   logged-out sessions are rejected server-side.
5. On OAuth failure the callback redirects to `/login?error=<message>` instead of
   returning raw JSON, so the user sees a friendly error page.
6. `/auth/logout` deletes the session row, so a stolen cookie cannot be replayed.

On Vercel, the Postgres `DATABASE_URL` may include `sslmode=require&channel_binding=require`
query params. These are stripped and mapped to asyncpg's `ssl=True` connect arg by
`app/database/connection.py` (asyncpg rejects raw `sslmode`/`channel_binding` kwargs).

## Database

| Environment | URL | Notes |
|-------------|-----|-------|
| Development | `sqlite:///./screening.db` | Default, zero config |
| Production | `postgresql+asyncpg://...` (Neon) | Free tier, autoscaling |

Schema is defined in `app/database/schema.py`; use Alembic for migrations
(`alembic revision --autogenerate`).

## Vercel observability, analytics & bot protection

- **Web Analytics** and **Speed Insights** are wired into the React SPA in
  `ui/src/main.tsx` (`@vercel/analytics/react` + `@vercel/speed-insights/react`).
- **BotID** (serverless bot protection) is enabled in the **Vercel dashboard**
  (Project → Security → BotID). The `botid` npm package only works with Next.js
  API routes, so this FastAPI + Vite stack uses the dashboard-level setting instead.

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
- Config: `vercel.json` builds the UI, serves static assets, and routes to the API
  function with a 300s max duration
- Serverless-aware design: cached config singleton, minimal top-level imports,
  conservative DB pooling, in-process JD caching to avoid repeat LLM cost.

```bash
uv run vercel --prod      # static UI + API function in one deploy
```

## Roadmap

- [x] Modular backend with provider-agnostic LLM agents
- [x] React (Vite) frontend mounted to the FastAPI API
- [x] Google OAuth sign-in with DB-backed sessions + server-side Google JWT
- [x] Persistence (SQLite dev / Neon Postgres prod), result + JD repositories
- [x] Vercel Web Analytics + Speed Insights, BotID protection
- [ ] Batch/parallel resume screening
- [ ] Storage backend selection (Vercel Blob vs AWS S3) for saved resumes

## License

MIT
