# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

E-Tech AI Research Assistant — a SaaS platform that runs a 5-agent LangGraph pipeline to produce citation-backed research reports. Frontend: Next.js 15 App Router. Backend: FastAPI + LangGraph.

## Commands

### Backend

```bash
cd backend
py -m venv .venv && .venv\Scripts\activate    # Windows venv
pip install -r requirements.txt
cp .env.example .env                           # then fill API keys
py -m uvicorn main:app --reload --port 8000
```

Run a single file / test:
```bash
py -c "import asyncio; from app.agents.planner import planner_node; ..."
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local              # fill NEXTAUTH_SECRET
npm run dev                                    # http://localhost:3000
```

### Docker (full stack)

```bash
cp backend/.env.example .env                  # set ANTHROPIC_API_KEY + TAVILY_API_KEY
docker compose up --build
```

## Architecture

```
backend/
  main.py                     FastAPI app entrypoint, lifespan creates tables
  app/
    config.py                 Pydantic-settings config; DATABASE_URL switches SQLite↔PG
    database.py               AsyncEngine + AsyncSessionLocal; create_tables()
    models/                   SQLAlchemy 2.0 Mapped[] models (User, Report, Source, AgentRun, SavedReport)
    schemas/                  Pydantic v2 request/response schemas
    agents/
      state.py                ResearchState TypedDict — the shared graph state
      graph.py                LangGraph StateGraph; error-exits via conditional edges
      planner.py              Claude claude-sonnet-4-6 → JSON queries + subtopics
      search.py               Tavily + arxiv in parallel; deduplication by URL
      validator.py            Claude scores sources; domain heuristic for credibility
      extractor.py            HTTP fetch + Claude Haiku per source (concurrent)
      synthesizer.py          Claude claude-sonnet-4-6 → full markdown report
    api/v1/                   auth / research / reports / export routers
    services/
      research_service.py     Runs graph.astream(); SSE via asyncio.Queue per report_id
      export_service.py       markdown → PDF via WeasyPrint

frontend/src/
  app/
    (auth)/                   sign-in / sign-up (no layout wrapper)
    (dashboard)/              layout with Sidebar; all protected routes
      research/[id]/          SSE listener + AgentTimeline + ReportViewer
  components/
    research/                 ResearchInput, AgentTimeline, ReportViewer
    landing/                  Hero, Features, HowItWorks, Pricing, FAQ, Footer
    layout/                   Sidebar, Header, MobileHeader
  hooks/
    use-sse.ts                EventSource hook; maps SSE events to AgentStep[]
    use-research.ts           TanStack Query mutations/queries wrapping api.ts
  lib/
    api.ts                    axios client; interceptor attaches JWT from NextAuth session
    auth.ts                   NextAuth v5 with CredentialsProvider → FastAPI JWT
```

## Key patterns

- **Auth flow**: NextAuth CredentialsProvider calls `POST /api/v1/auth/login`, stores JWT in session. `apiClient` interceptor reads `session.user.access_token` for every request.
- **SSE streaming**: `research_service.py` holds `_progress_queues: dict[str, asyncio.Queue]`. `run_research()` background task writes events; `stream_progress()` generator reads them. Frontend uses native `EventSource`.
- **LangGraph error routing**: After every node, `_should_continue()` checks `state["error"]`; routes to END on error, stopping the pipeline.
- **DB switching**: Set `DATABASE_URL=sqlite+aiosqlite:///./research.db` for local dev (zero config); set PostgreSQL URL for prod. SQLAlchemy connect_args differ per dialect.
- **Agent model choice**: Synthesizer/Planner/Validator use `gemini-2.0-flash` (quality). Extractor uses `gemini-2.0-flash-lite` (speed/cost) since it runs once per source.

## Required environment variables

Backend `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=tvly-...
SECRET_KEY=<random 32+ chars>
DATABASE_URL=sqlite+aiosqlite:///./research.db
```

Frontend `.env.local`:
```
NEXTAUTH_SECRET=<random 32+ chars>
NEXTAUTH_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```
