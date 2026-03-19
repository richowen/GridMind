# GridMind — Overview & Project Structure

## Workspace Reorganisation

The current GitHub repo (`Battery December 2025`) is reorganised **in-place**:

```
Battery December 2025/          ← This GitHub repo (stays as-is for git history)
│
├── legacy/                     ← NEW: all existing files moved here
│   ├── backend/                ← V2 Python backend (reference)
│   ├── nodered/                ← Node-RED flows (reference)
│   ├── flows.json              ← Original flows
│   ├── *.md                    ← Old documentation
│   └── ...                     ← All other existing files
│
├── gridmind/                   ← NEW: clean GridMind project
│   ├── backend/
│   ├── frontend/
│   ├── database/
│   ├── docker-compose.yml
│   ├── .env.example
│   └── README.md
│
└── plans/                      ← STAYS: architecture planning docs
    ├── GRIDMIND_00_INDEX.md
    ├── GRIDMIND_01_OVERVIEW.md
    └── ...
```

**Git history is preserved** — the repo continues as normal. The `legacy/` folder is just a reorganisation of existing files. The `gridmind/` folder is the new clean project.

---

## What Changes and Why

### Current Limitations (Node-RED V2)

| Problem | Impact |
|---------|--------|
| Node-RED dashboard is basic — limited charting | Poor data visibility |
| Flows are hard to maintain and debug | Fragile automation |
| No proper schedule editor UI | Manual JSON editing |
| No temperature-aware immersion control | Wasted energy |
| Node-RED is a separate dependency | Extra complexity |
| No history/analytics views | Can't review decisions |
| Hardcoded thresholds in Python code | Requires code changes to tune |
| Fixed to exactly 2 immersions | Not extensible |
| Export price formula is wrong (% of import) | Suboptimal decisions |
| Constant 2kW load assumption | Not configurable via UI |

### What Gets Eliminated
- All Node-RED flows (`nodered/` directory becomes legacy archive)
- Node-RED dependency entirely
- All hardcoded thresholds (price limits, SOC limits, solar limits)
- Wrong export price formula
- Constant load assumption

### What Gets Kept (Reused in GridMind)
- LP optimization engine logic (from `optimizer.py`)
- Home Assistant API client patterns
- Octopus Energy API client
- InfluxDB client (with identical measurement schema)
- MariaDB database (existing data preserved)

---

## Project Structure

GridMind is a **clean new project** in a `gridmind/` directory. The existing workspace stays as archive — no legacy code mixed in.

```
gridmind/
│
├── README.md
├── docker-compose.yml
├── .env.example                   ← Minimal: DB creds + log level only
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       ├── 001_initial_schema.py      ← prices, optimization, system_state
│   │       ├── 002_immersion_devices.py   ← device registry
│   │       ├── 003_rules_engine.py        ← smart rules + temp targets
│   │       ├── 004_overrides.py           ← manual overrides
│   │       ├── 005_system_actions.py      ← audit log
│   │       └── 006_system_settings.py     ← all config in DB
│   └── app/
│       ├── __init__.py
│       ├── main.py                        ← FastAPI app + lifespan (~40 lines)
│       ├── config.py                      ← Minimal pydantic settings (~20 lines)
│       ├── database.py                    ← SQLAlchemy engine + session (~30 lines)
│       │
│       ├── models/                        ← SQLAlchemy ORM models by domain
│       │   ├── __init__.py
│       │   ├── prices.py                  ← (~30 lines)
│       │   ├── optimization.py            ← (~40 lines)
│       │   ├── immersion.py               ← Device, SmartRule, TempTarget (~50 lines)
│       │   ├── overrides.py               ← (~30 lines)
│       │   ├── actions.py                 ← (~25 lines)
│       │   └── settings.py                ← (~20 lines)
│       │
│       ├── schemas/                       ← Pydantic request/response schemas
│       │   ├── __init__.py
│       │   ├── prices.py
│       │   ├── optimization.py
│       │   ├── immersion.py
│       │   ├── overrides.py
│       │   ├── settings.py
│       │   └── system.py
│       │
│       ├── routers/                       ← Thin FastAPI route handlers
│       │   ├── __init__.py
│       │   ├── optimization.py            ← /api/v1/recommendation, /prices, /state
│       │   ├── immersion.py               ← /api/v1/immersions/* (devices, rules, targets)
│       │   ├── overrides.py               ← /api/v1/overrides/*
│       │   ├── history.py                 ← /api/v1/history/*, /api/v1/actions
│       │   └── system.py                  ← /api/v1/system/* (health, settings)
│       │
│       ├── services/                      ← External integrations
│       │   ├── __init__.py
│       │   ├── home_assistant.py
│       │   ├── octopus_energy.py
│       │   └── influxdb.py
│       │
│       ├── core/                          ← Business logic
│       │   ├── __init__.py
│       │   ├── optimizer.py               ← LP engine (fixed export price + constant load)
│       │   ├── rules_engine.py            ← Configurable immersion rules (no schedules)
│       │   ├── action_executor.py         ← Applies decisions to HA
│       │   ├── scheduler.py               ← APScheduler jobs (with error handling)
│       │   └── settings_cache.py          ← In-memory settings cache (60s TTL)
│       │
│       └── websocket/
│           ├── __init__.py
│           └── manager.py
│
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── pages/
│       │   ├── Dashboard.tsx
│       │   ├── Prices.tsx
│       │   ├── Immersions.tsx
│       │   ├── History.tsx
│       │   ├── Controls.tsx
│       │   └── Settings.tsx
│       ├── components/
│       │   ├── layout/
│       │   ├── dashboard/
│       │   ├── charts/
│       │   ├── immersion/
│       │   └── ui/                        ← shadcn/ui components
│       ├── hooks/
│       │   ├── useWebSocket.ts
│       │   ├── useApi.ts
│       │   └── useLiveState.ts
│       ├── api/
│       │   ├── client.ts
│       │   ├── optimization.ts
│       │   ├── immersion.ts
│       │   ├── overrides.ts
│       │   └── history.ts
│       └── types/
│           ├── api.ts
│           └── domain.ts
│
└── database/
    └── seed_data.sql                      ← Initial immersion device data
```

---

## Technology Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| Backend API | Python FastAPI | Async, fast, auto-docs |
| Scheduler | APScheduler 3.x | In-process, no broker needed |
| LP Optimizer | PuLP + CBC | Proven, fast |
| Rules Engine | Python (new) | Evaluates DB-stored rules |
| DB Migrations | Alembic | Versioned, repeatable |
| Database | MariaDB | Existing data preserved |
| Time-series | InfluxDB | Existing Grafana dashboards preserved |
| Frontend | React 18 + TypeScript | Best dashboard ecosystem |
| Build tool | Vite | Fast builds |
| UI Components | shadcn/ui + Tailwind CSS | Polished, accessible |
| Charts | Recharts | React-native, responsive |
| Real-time | WebSocket (FastAPI native) | No extra dependencies |
| Frontend server | Nginx | SPA routing + API proxy |
| Container | Docker + docker-compose | Existing deployment method |

---

## Key Design Principles

1. **Zero hardcoded values** — all thresholds, entity IDs, and config in DB, editable via UI
2. **N immersion devices** — not fixed to main + lucy, add any number
3. **Temperature targets over schedules** — "ensure X°C by Y time" replaces fixed weekly time windows
4. **InfluxDB backward compatible** — existing Grafana dashboards work unchanged
5. **Clean separation** — no legacy code in GridMind directory
6. **Alembic migrations** — database changes are versioned and repeatable
7. **Configurable load assumption** — constant kW value editable in UI, no CT clamps needed
8. **Correct export price** — fixed SEG rate, not percentage of import price
9. **AI-optimised codebase** — small focused files, clear boundaries, minimal token cost

---

## AI Coding Guidelines

This codebase is **entirely AI-coded**. Every file is designed for AI agents to read, create, and edit efficiently. These guidelines minimise token usage and reduce errors.

### File Size Targets

| Layer | Target Lines | Rationale |
|-------|-------------|-----------|
| Backend models | 30-60 | One domain per file |
| Backend schemas | 30-60 | Pydantic models separate from ORM |
| Backend routers | 50-100 | Thin handlers, delegate to services/core |
| Backend services | 50-100 | One external integration per file |
| Backend core logic | 80-150 | Split if larger |
| Frontend pages | 50-100 | Compose components, minimal logic |
| Frontend components | 30-80 | Single responsibility |
| Frontend hooks | 20-50 | One hook per file |
| Frontend API clients | 20-40 | One domain per file |
| Frontend types | 20-50 | One domain per file |

### Coding Conventions

- **One concern per file** — never mix domains or responsibilities
- **Brief docstring at file top** — 1-2 lines explaining purpose and key dependencies
- **Explicit imports** — no wildcard imports, no re-exports through `__init__.py` barrels
- **Typed function signatures** — all parameters and return types annotated
- **Consistent patterns** — all routers follow the same structure, all models follow the same structure
- **No monolithic files** — if a file exceeds its target, split it
- **Descriptive file names** — the file name should tell you what it does without opening it
- **Separate ORM models from Pydantic schemas** — `models/` for SQLAlchemy, `schemas/` for Pydantic
