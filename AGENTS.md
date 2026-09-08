<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
| ------ | ---------- |
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.

---

<!-- backend architecture & migration notes -->
## Backend (app/) — Architecture & Database Migrations

### Overview & Multi-Agent Pipeline
The backend is built with **FastAPI** (`app/main.py`), utilizing `app.frontend("/", directory=UI_DIST)` to serve the compiled Vite single-page application (`ui/dist`) directly alongside the API routes (`/api/v1/*`).

Key Backend Components:
- **Agent Orchestrator** (`app/agents/orchestrator.py`): Coordinates the candidate extraction, job description resolution, evaluation, and review agent pipelines (`BrutalReviewAgent`, `ATSOptimizerAgent`, `BulletPointTransformerAgent`, `IndustryToneMatchAgent`, `FinalPolishAgent`).
- **Database Layer**: SQLAlchemy 2.0 async sessions (`AsyncSession`) using repositories (`app/database/repositories/`).
- **BYOK AI Providers**: Decrypted user API key support allowing users to bring their own OpenAI, Anthropic, or OpenCode Zen model credentials.

### Database Migrations (Alembic)
Migrations are managed via **Alembic** under `migrations/`.
- Current head revision: `a1b2c3d4e5f6` (`add_review_edit_chat_app_tables`).
- To apply migrations: `uv run alembic upgrade head`
- Schema definitions: Defined in `app/database/schema.py` covering users, sessions, screening_results, job_descriptions, resume_reviews, resume_edit_sessions, resume_chat_sessions, job_applications, and external_jobs.

---

<!-- frontend stack notes -->
## Frontend (ui/) — Tailwind CSS v4 & Chat-First Workspace

The `ui/` app uses **Tailwind CSS v4** with the Vite plugin and TanStack Router.

- **Chat-First UI (`/screen`)**: The screening workspace presents an interactive AI Chatbot interface first, supporting inline PDF/DOCX document uploads, text pasting, live demo runners, quick prompt chips, and 1-click edit applications.
- **Hero & Landing State**: Features a glowing gradient orb header, central input container with in-card action pills (`Attach`, `Search`, `Reason`, `Voice`), quick prompt chips (`Optimize Resume`, `Analyze ATS Gaps`, `Bullet Transformer`, `Senior Tone Match`), and 1-click demo execution.
- **Split-Screen Canvas Workspace**:
  - **Left Chat Rail**: Live multi-agent progress ticker (`[1/5]` to `[5/5]`), collapsible reasoning thought blocks (`Thought for 7s` with 5-agent trace), live generative stream status indicator, and line-targeted prompt dispatch.
  - **Right Canvas Panel (`WorkspacePanel.tsx`)**: Executive KPI Score Cards (**ATS Match Score %**, **Tone Alignment %**, **Quality Score %**) alongside full 5-agent findings (`CvReviewResults.tsx`) and line-numbered document editor (`ResumeDocument.tsx`).
- **No `tailwind.config.ts`** — theme is CSS-first, defined in `ui/src/styles/index.css` via `@theme inline { ... }` mapping to CSS variables.
- **No `postcss.config.js`** — Tailwind runs as `@tailwindcss/vite` plugin in `ui/vite.config.ts`.
- Entry point: `@import "tailwindcss";` at the top of `ui/src/styles/index.css`.
- Custom utilities use the v4 `@utility` directive (e.g. `scrollbar-none`).

---

<!-- memory & handover checklist -->
## Agent Memory & Tomorrow's Build TODO Checklist

### Completed In Today's Session
- [x] **Hero Landing State (`CvBuilder.tsx`)**: Glowing gradient orb header (`What Can I help with?`), central card input with in-card action pills (`Attach`, `Search`, `Reason`, `Voice`), quick prompt chips (`Optimize Resume`, `Analyze ATS Gaps`, `Bullet Transformer`, `Senior Tone Match`), and demo runner.
- [x] **Conversational Flow Transition**: Seamless single-flow transition from Page 1 (Hero State) into Page 2 (Split-screen session workspace), carrying prompt + CV text/file + target Job Description (JD).
- [x] **Live Generative Stream UI (`ChatMessages.tsx`)**: Real-time 5-agent stage progress ticker (`[1/5]` to `[5/5]`), collapsible reasoning thought blocks (`Thought for 7s`), and live generative stream status badge.
- [x] **Split-Screen Canvas Dashboard (`WorkspacePanel.tsx`)**: Executive KPI metric cards (**ATS Match Score %**, **Tone Alignment %**, **Quality Score %**) above 5-agent report breakdown & line editor.
- [x] **Build Verification**: `npm run typecheck && npm run build` verified with 0 errors; production bundle output to `ui/dist`.

### Tomorrow's Build TODO List
- [ ] Launch full backend server (`uvicorn app.main:app --reload`) and verify end-to-end API integration with BYOK LLM models.
- [ ] Test live streaming SSE endpoints for real-time token streaming in chat messages.
- [ ] Run full Cypress E2E suite (`npm run cypress:run`).


