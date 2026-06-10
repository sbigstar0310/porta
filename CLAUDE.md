# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Porta is a **LangGraph-based multi-agent investment analysis system** that analyzes users' stock portfolios and sends daily email reports (buy/sell/hold recommendations). No automatic trading — report-only with portfolio management. US stocks only.

## Tech Stack

- **Backend**: Python 3.10+ / FastAPI / Uvicorn / uv (package manager)
- **Frontend**: Flutter (BLoC state management, go_router)
- **AI Agents**: LangGraph + LangChain + OpenAI GPT
- **Database**: Supabase (PostgreSQL + Auth + RLS)
- **Background Jobs**: Celery + Redis (celery-redbeat for scheduling)
- **Email**: Resend API + WeasyPrint (PDF generation)
- **Infrastructure**: Docker Compose, Nginx reverse proxy

## Common Commands

### Backend
```bash
cd backend
uv sync                              # Install dependencies
uv run ./scripts/run-server.sh       # Start dev server (auto-reload)
uv run ./scripts/run-celery.sh       # Start Celery worker
uv run pytest tests/                 # Run all tests
uv run pytest tests/ -m unit         # Run only unit tests
uv run pytest tests/test_file.py::test_name  # Run single test
```

### Frontend
```bash
cd frontend
flutter pub get                      # Install dependencies
flutter run -d web-server --web-port 3000  # Run web dev server
flutter analyze                      # Lint
flutter test                         # Run tests
```

### Docker Stack
```bash
./scripts/stack-start.sh             # Start dev
./scripts/stack-start.sh --prod      # Start production
./scripts/stack-stop.sh              # Stop
./scripts/stack-logs.sh [service]    # View logs (api, worker, beat, redis, nginx)
./scripts/stack-restart.sh           # Restart
```

## Architecture

### Backend (Clean Layered)
```
backend/
  routers/        → FastAPI endpoint handlers (auth, portfolio, position, agent, stock, report, schedule)
  usecase/        → Business logic layer
  repo/           → Repository pattern (data persistence)
  data/           → Models (Pydantic), schemas (request/response), DB singleton
  clients/        → External service integrations (supabase, email, stock, cache)
  graph/          → LangGraph agent pipeline
    root_graph.py → Orchestrates all agents
    agents/       → Individual agents (crawler, momo, fund, reviewer, risk, decider, reporter)
    llm_clients/  → LLM provider configurations
  worker/         → Celery app, tasks, config
  dependencies/   → FastAPI dependency injection (auth)
  scripts/        → Backend dev server scripts (run-server, run-celery)
```

### Agent Pipeline Flow
```
START → CRAWLER (news/market data) → MOMO (momentum) ─┐
                                   → FUND (fundamental)├→ RISK MANAGER → DECIDER → REPORTER → END
      → REVIEWER (historical)  ────────────────────────┘
```
Crawler, Momo, and Fund run in parallel. Reviewer runs independently. All feed into Risk Manager.

### Frontend (BLoC Pattern)
```
frontend/lib/
  bloc/           → State management (auth, portfolio, agent, position, health, settings)
  screens/        → UI pages
  services/       → DioClient (HTTP), StorageService
  models/         → Data classes
  widgets/        → Reusable components
  constants/      → Colors, strings
```

### Database Tables
- `users` — email, timezone, language (synced from Supabase Auth)
- `portfolios` — one per user, base_currency, cash
- `transactions` — buy/sell records with ticker, shares, price
- `reports` — agent-generated markdown reports
- `schedules` — user-configured report time (hour, minute, timezone)

## Conventions

### Commit Messages
Format: `[type:scope] Description`
- Types: `feat`, `fix`, `refactor`, `docs`
- Scopes: `frontend`, `backend`, `docker`, `nginx`, `scripts`, `documents`
- Examples: `[feat:backend] Add email verification endpoint`, `[fix:frontend] Fix login state handling`

### Backend Patterns
- Authentication via Supabase JWT, injected with `Depends(get_current_user_id)`
- Async throughout (AsyncIO + SQLAlchemy async)
- API docs available at `http://localhost:8000/docs` (Swagger)
- Supabase clients (`clients/supabase_client.py`): auth ops (sign-in/up) use the **anon** key (`SUPABASE_KEY`); data repos use the **service_role** key (`SUPABASE_SERVICE_ROLE_KEY`) via `get_supabase_admin_client()` — `repo/__init__.py:get_db_client()` returns the admin client to bypass RLS, since the backend enforces auth itself. Do not set the two keys equal.

### Frontend Patterns
- BLoC for all state management (Events → Bloc → States)
- go_router for navigation
- Dio for HTTP requests with interceptors
- flutter_secure_storage for tokens

## Environment Variables (root .env)

Required: `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY` (anon), `SUPABASE_SERVICE_ROLE_KEY` (service_role — data layer/RLS bypass), `RESEND_API_KEY`, `REDIS_URL`
Optional: `LANGSMITH_API_KEY` (agent tracing), `ANTHROPIC_API_KEY`, `FINNHUB_API_KEY` (news/earnings calendar/price fallback — without it, crawler uses web search only and the earnings-blackout rule is skipped; free tier is personal-use, needs commercial license before monetization)

## Test Markers (pytest)

`unit`, `integration`, `e2e`, `agent`, `db`, `api`, `slow`

Usage: `uv run pytest tests/ -m "unit and not slow"`
