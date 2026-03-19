# GridMind

**Solar battery intelligence system** — replaces Node-RED V2 with a modern FastAPI + React stack.

## Quick Start

```bash
# 1. Copy and configure environment
cp .env.example .env
# Edit .env with your DB credentials

# 2. Start all services
docker-compose up -d

# 3. Access the UI
open http://192.168.1.2:3000
```

## Architecture

```
Browser :3000 (React + Tailwind)
    ↕ REST + WebSocket
Backend :8000 (FastAPI + APScheduler)
    ↕ SQL
MariaDB :3306 (gridmind database)
    ↕ HTTP
InfluxDB :8086 (time-series metrics)
    ↕ HTTP
Home Assistant :8123 (Fox inverter + immersions)
```

## Key Features

- **LP Optimizer** — 24-48hr price lookahead, fixed SEG export price (not % of import)
- **Configurable load assumption** — constant kW value editable in Settings UI
- **N immersion devices** — not fixed to 2; add any number via UI
- **Temperature targets** — "ensure X°C by Y time" replaces fixed schedules
- **Configurable rules engine** — all thresholds in DB, editable via UI
- **WebSocket real-time** — dashboard updates live without polling
- **Full audit log** — every HA call logged to `system_actions` table
- **Zero hardcoded values** — all config in DB, editable via Settings page

## Services

| Service | URL | Purpose |
|---------|-----|---------|
| GridMind UI | http://192.168.1.2:3000 | Main web interface |
| API | http://192.168.1.2:8000 | REST API |
| API Docs | http://192.168.1.2:8000/docs | Swagger UI |
| InfluxDB | http://192.168.1.2:8086 | Time-series DB |

## First-Time Setup

1. Start containers: `docker-compose up -d`
2. Alembic migrations run automatically on backend startup
3. Open Settings page and configure:
   - Home Assistant URL + token
   - Octopus Energy product/tariff/region codes
   - Battery capacity and limits
4. Click "Test HA Connection" to verify
5. Click "Refresh Prices" to fetch initial Agile prices
6. Automation starts immediately (every 5min optimization, every 1min immersion evaluation)

## Development

```bash
# Backend only (hot-reload via volume mount)
docker-compose up backend mariadb

# Frontend dev server
cd frontend && npm install && npm run dev
```

## Project Structure

```
gridmind/
├── backend/
│   ├── app/
│   │   ├── core/          # Business logic (optimizer, rules engine, scheduler)
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── routers/       # FastAPI route handlers
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   ├── services/      # External integrations (HA, Octopus, InfluxDB)
│   │   └── websocket/     # WebSocket manager
│   └── alembic/           # Database migrations
├── frontend/
│   └── src/
│       ├── api/           # API client functions
│       ├── components/    # React components
│       ├── hooks/         # Custom React hooks
│       ├── pages/         # Page components
│       └── types/         # TypeScript types
└── database/
    └── seed_data.sql      # Reference seed data (handled by Alembic)
```
