# Sovela AI — Universal AI Life Operating System (Prototype v1)

**Sovela AI** is a full-stack personal productivity, learning, and opportunity platform that unifies goal decomposition, deterministic daily time-blocking, missed-task recovery, curated learning roadmaps, skill assessments, Socratic AI mentorship, and categorized opportunity discovery into one cohesive workspace.

This repository contains the **First Working Prototype (v1)** built with a **FastAPI** asynchronous backend and a **Next.js 15 / React 19** frontend.

---

## Key Capabilities (Prototype v1)

- **Authentication & Guided Onboarding:**
  - Email/password registration and login backed by `bcrypt` password hashing and stateless `HS256` JWT tokens.
  - 4-step interactive **Onboarding Wizard** (persona selection, daily focus capacity, interest domains, primary goal & mentorship interaction style) plus profile and password management.
- **Today Dashboard & Task Execution:**
  - Unified daily execution view (`/api/v1/dashboard/today`) aggregating active goals, scheduled tasks, completion states, and a client-side focus timer.
  - Task CRUD supporting priority (`1–4`), duration estimates, energy requirements (`1–5`), and scheduled timestamps.
- **Deterministic Temporal Scheduling & Recovery Engines:**
  - **Knapsack Interval Scheduler (`KnapsackScheduler`):** Sanitizes/merges overlapping free intervals, prevents booking collisions with an inter-task buffer, strictly enforces per-user daily capacity limits, and surfaces unplaceable tasks transparently.
  - **Intelligent Missed-Task Recovery (`IMTRRecoveryEngine`):** Redistributes overdue tasks across `D+1` to `D+3` via greedy load-smoothing without silently exceeding daily capacity limits, explicitly reporting any deferred overflow tasks.
- **Goals & AI Decomposition:**
  - Goal lifecycle CRUD (`career`, `skill`, etc.) with automated breakdown into actionable subtasks (`POST /api/v1/goals/{goal_id}/decompose`).
- **Learning Management (Roadmaps, Skills & Assessments):**
  - Idempotently seeded curated learning roadmaps (such as `full-stack-ai-engineering`), step-by-step curriculum modules, roadmap enrollment, node progress tracking, verified skill competencies portfolio, and interactive knowledge assessments (`GET /api/v1/learning/assessments/node/{node_id}`, `POST /api/v1/learning/assessments/{assessment_id}/submit`).
- **Socratic AI Mentor & Dual-Provider Router:**
  - Persistent multi-turn Socratic chat sessions (`/api/v1/intelligence/socratic/*`) powered by `AIRouterService`.
  - Features provider adapters (`OpenAIProvider`, `GeminiProvider`, `AnthropicProvider`, plus deterministic `SimulationProvider` for offline development and automated tests) and a **200ms Time-To-First-Byte (TTFB) abort probe** that monitors chunk-0 delivery and automatically fails over from the primary model to the fallback model on timeout or provider error.
- **Opportunity Hub (8 Categories):**
  - Filterable catalog covering all 8 opportunity categories (`internship`, `job`, `hackathon`, `contest`, `scholarship`, `grant_fellowship`, `research_post`, `event`) with search filtering and seeded catalog initialization (`ENABLE_LIVE_SCRAPING=False` in Prototype v1).

---

## System Architecture

### High-Level Component Architecture

```mermaid
flowchart TD
    subgraph Client["Client Layer — Next.js 15 / React 19 SPA"]
        Nav["Navigation & Shell (page.tsx)"]
        UI_Today["Today & Plan + Pomodoro Timer"]
        UI_Learn["Roadmaps, Skills & Assessments"]
        UI_Goals["Goals & Milestones Manager"]
        UI_Mentor["Socratic Mentor Chat"]
        UI_Opp["Opportunity Hub (8 Categories)"]
        UI_Auth["Auth Modal & 4-Step Onboarding"]
        APIClient["REST Client (frontend/src/lib/api.ts)"]

        Nav --> UI_Today & UI_Learn & UI_Goals & UI_Mentor & UI_Opp & UI_Auth
        UI_Today & UI_Learn & UI_Goals & UI_Mentor & UI_Opp & UI_Auth --> APIClient
    end

    subgraph Mobile["Future Mobile Target (Next Milestone)"]
        APK["Android APK Wrapper (Capacitor / WebView)"]
        APK -. "Reuses decoupled REST UI + NEXT_PUBLIC_API_URL" .-> Client
    end

    subgraph API["API Gateway — FastAPI (/api/v1)"]
        CORS["CORS Middleware (Explicit Origins)"]
        AuthGuard["JWT Bearer Guard (deps.py / security.py)"]
        R_Auth["/auth"]
        R_Dash["/dashboard"]
        R_Goals["/goals"]
        R_Tasks["/tasks"]
        R_Temp["/temporal"]
        R_Intel["/intelligence"]
        R_Learn["/learning"]
        R_Opp["/opportunities"]

        CORS --> AuthGuard
        AuthGuard --> R_Auth & R_Dash & R_Goals & R_Tasks & R_Temp & R_Intel & R_Learn & R_Opp
    end

    subgraph Services["Domain Services & AI Orchestration"]
        Sched["KnapsackScheduler (scheduler.py)"]
        IMTR["IMTRRecoveryEngine (imtr.py)"]
        Router["AIRouterService (ai_router.py)\n200ms TTFB Abort Probe"]
        P_Sim["SimulationProvider (Offline/Tests)"]
        P_OAI["OpenAIProvider (gpt-4o-mini-2024-07-18)"]
        P_Gem["GeminiProvider (gemini-3.5-flash-lite)"]
        P_Ant["AnthropicProvider (claude-haiku-5-5)"]

        R_Temp --> Sched & IMTR
        R_Intel & R_Goals --> Router
        Router -->|Primary / Socratic| P_OAI & P_Ant
        Router -->|Fallback on TTFB Breach / Error| P_Gem
        Router -->|Simulation Mode| P_Sim
    end

    subgraph Data["Persistence & Migration Layer"]
        ORM["Async SQLAlchemy 2.0 (16 ORM Models)"]
        Alembic["Alembic Migrations (3 Revisions)"]
        SQLite[("SQLite + aiosqlite (Local Dev)")]
        PG[("PostgreSQL 16 + pgvector / Redis\n(infra/docker-compose.yml)")]

        API & Services --> ORM
        ORM --> SQLite
        ORM -. "DATABASE_URL" .-> PG
        Alembic --> ORM
    end

    APIClient -->|"HTTP/JSON + Bearer JWT"| CORS
```

### AI Router Failover Architecture

`AIRouterService` separates **Connection Establishment**, **TTFB (receipt of first stream chunk)**, and **Total Turnaround Time**:
1. In `simulation` mode (default for local offline development and CI tests), deterministic `SimulationProvider` adapters respond cleanly without requiring external API keys.
2. In `live` mode (with provider API keys set in `.env`), requests stream through the primary adapter (`gpt-4o-mini-2024-07-18` for triage or `claude-haiku-5-5` for Socratic mentoring).
3. If chunk 0 does not arrive within `LLM_TTFB_ABORT_THRESHOLD_MS` (`200ms`), the active generator stream is cancelled and execution immediately fails over to `gemini-3.5-flash-lite`.

---

## Database Schema (16 Models)

Managed via SQLAlchemy 2.0 async sessions and **Alembic** (`backend/alembic/versions/`):

| Domain | Tables |
| :--- | :--- |
| **Users & Profiles** | `users`, `user_profiles` |
| **Goals & Execution** | `goals`, `milestones`, `tasks` |
| **AI Mentorship** | `chat_sessions`, `chat_messages` |
| **Learning & Skills** | `roadmaps`, `roadmap_nodes`, `roadmap_enrollments`, `user_node_progress`, `skills`, `user_skills`, `assessments`, `user_assessment_attempts` |
| **Opportunity Hub** | `opportunities` |

Migration chain: `e7657f9cf5b6` (initial schema) $\rightarrow$ `f8910a11b123` (chat sessions) $\rightarrow$ `feb5a66bac13` (learning management schema).

---

## API Surface Overview

All routes are served under `/api/v1` (except `/health`):

- **System:** `GET /health`
- **Auth & Profile (`/auth`):** `POST /register`, `POST /login`, `GET /me`, `PUT /profile`, `POST /onboarding`, `PUT /change-password`
- **Dashboard (`/dashboard`):** `GET /today`
- **Goals (`/goals`):** `GET /`, `POST /`, `GET /{goal_id}`, `PUT /{goal_id}`, `DELETE /{goal_id}`, `POST /{goal_id}/decompose`
- **Tasks (`/tasks`):** `GET /`, `POST /`, `GET /{task_id}`, `PUT /{task_id}`, `DELETE /{task_id}`, `PUT /{task_id}/complete`
- **Temporal Engines (`/temporal`):** `POST /auto-schedule`, `POST /imtr/rebalance`
- **Socratic Mentor (`/intelligence/socratic`):** `POST /chat`, `GET /sessions`, `POST /sessions`, `GET /sessions/{session_id}`, `DELETE /sessions/{session_id}`, `POST /sessions/{session_id}/message`
- **Learning Management (`/learning`):** `GET /roadmaps`, `GET /roadmaps/{slug_or_id}`, `POST /roadmaps/{roadmap_id}/enroll`, `POST /nodes/{node_id}/complete`, `GET /skills`, `GET /assessments/node/{node_id}`, `POST /assessments/{assessment_id}/submit`
- **Opportunities (`/opportunities`):** `GET /`, `POST /seed`

Interactive Swagger documentation is available at `http://127.0.0.1:8000/docs` when the backend is running.

---

## Repository Structure

```text
.
├── .env.example                 # Environment variable template
├── .gitignore                   # Git exclusion rules
├── README.md                    # Prototype architecture & setup guide
├── alembic.ini                  # Alembic migration configuration
├── requirements.txt             # Python backend dependencies
├── backend/
│   ├── alembic/                 # Database migration environment & versions
│   ├── app/
│   │   ├── api/                 # Auth dependencies & v1 REST routers
│   │   ├── core/                # Pydantic settings & security (bcrypt/PyJWT)
│   │   ├── db/                  # Async engine/session & seed scripts
│   │   ├── models/              # 16 SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/            # Knapsack scheduler, IMTR, AI router & providers
│   │   └── main.py              # FastAPI entrypoint, CORS, router registration
│   └── tests/
│       ├── benchmarks/          # Scheduler, IMTR, and AI router benchmarks
│       ├── integration/         # End-to-end API, onboarding, learning flows
│       └── unit/                # Auth, isolation, migrations, and service unit tests
├── frontend/
│   ├── package.json             # Next.js 15, React 19, Tailwind CSS, Lucide icons
│   ├── tailwind.config.js       # Custom theme tokens
│   └── src/
│       ├── app/                 # App Router entry (layout.tsx, page.tsx, globals.css)
│       ├── components/          # Auth, Onboarding, TodayView, Goals, Learning, Mentor, Opportunities, Profile
│       └── lib/api.ts           # Typed fetch wrapper & session management
└── infra/
    └── docker-compose.yml       # PostgreSQL 16 (pgvector) & Redis services
```

---

## Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python 3.13, FastAPI `0.137.2`, Uvicorn `0.49.0`, Pydantic `2.10.6`, SQLAlchemy `2.0.43`, Alembic `1.20.1` |
| **Auth & Crypto** | `bcrypt 5.0.0`, `PyJWT 2.10.1` |
| **Database** | SQLite (`aiosqlite 0.22.1`) for local dev; PostgreSQL 16 (`pgvector/pgvector:pg16`) & Redis `7.2-alpine` configured in `infra/docker-compose.yml` |
| **Frontend** | Next.js `^15.1.0`, React `^19.0.0`, TypeScript `^5.7.2`, Tailwind CSS `^3.4.16`, `lucide-react` |
| **Testing** | `pytest 8.4.2`, `pytest-asyncio 0.25.3`, `httpx 0.28.1` |

---

## Getting Started (Local Development)

### Prerequisites
- **Python 3.11+** (tested on Python 3.13)
- **Node.js 20+** and **npm**
- *(Optional)* **Docker** if running PostgreSQL 16 + pgvector and Redis locally via `infra/docker-compose.yml`

### 1. Configure Environment
Copy `.env.example` to `.env` in the repository root and adjust values if enabling live LLM API keys:
```bash
cp .env.example .env
```
By default, the prototype runs offline-ready with SQLite (`sqlite+aiosqlite:///./sovela_dev.db`) and `AI_ROUTER_MODE=simulation`.

### 2. Backend Setup & Database Migrations
Install Python dependencies and apply Alembic migrations:

```bash
pip install -r requirements.txt
```

**Windows (PowerShell):**
```powershell
$env:PYTHONPATH = "backend"
python -m alembic -c alembic.ini upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**macOS / Linux:**
```bash
PYTHONPATH=backend python -m alembic -c alembic.ini upgrade head
PYTHONPATH=backend python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend API will be live at `http://127.0.0.1:8000` (Swagger UI: `http://127.0.0.1:8000/docs`).

### 3. Frontend Setup & Dev Server
In a second terminal:
```bash
cd frontend
npm install
npm run dev -- -p 3000
```
Open `http://localhost:3000` in your browser.

*(Optional)* Start PostgreSQL + pgvector and Redis containers:
```bash
docker compose -f infra/docker-compose.yml up -d
```
Then set `DATABASE_URL="postgresql+asyncpg://postgres:postgrespassword@localhost:5432/sovela_development"` in `.env` and run `alembic upgrade head`.

---

## Verification & Test Suite

### Run Backend Tests (44 Tests)
**PowerShell:**
```powershell
$env:PYTHONPATH = "backend"
python -m pytest backend/tests -v
```
**macOS / Linux:**
```bash
PYTHONPATH=backend python -m pytest backend/tests -v
```
Includes unit tests (auth, JWT security, ownership isolation, scheduler, IMTR, DDL compatibility, router failover), integration tests (E2E user flows, onboarding, learning roadmaps & assessments), and performance benchmarks.

### Run Frontend Production Build
```bash
cd frontend
npm run build
```

---

## Android APK Conversion Readiness (Next Milestone)

This repository currently targets the **Web Prototype v1** (`frontend/` + `backend/`) and **does not yet include an Android/Gradle build or prebuilt `.apk`**. However, the codebase is structured for clean packaging into an Android APK in the next milestone:

1. **Decoupled REST Client (`frontend/src/lib/api.ts`):** All frontend network calls route through a single `NEXT_PUBLIC_API_URL` environment variable with JSON + `Bearer` token headers, allowing an Android wrapper to target a hosted or LAN FastAPI backend cleanly.
2. **Static / WebView Packaging Path (e.g., Capacitor or TWA):**
   - Since all interactive screens live inside a client-side shell (`frontend/src/app/page.tsx`), enabling `output: "export"` in `next.config.mjs` allows exporting a static `out/` bundle suitable for wrapping in `@capacitor/android` (or pointing an Android WebView / TWA directly to the deployed HTTPS frontend URL).
3. **CORS Configuration for Mobile Origins:**
   - Update `CORS_ALLOWED_ORIGINS` in `.env` to include the Capacitor Android origin (`http://localhost` / `capacitor://localhost` or your deployed app origin) before generating an APK.
4. **Hardening Roadmap Beyond Prototype v1:**
   - Replace `localStorage` session persistence with encrypted native token storage (or HttpOnly cookies + CSRF for web deployments), connect `postgresql+asyncpg` in production, and configure live AI provider keys in `.env`.
