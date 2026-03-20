# GridMind

**Solar battery intelligence system** — FastAPI + React stack for optimising solar battery charging/discharging based on Octopus Agile pricing.

## Deployment

GridMind runs as two containers on Unraid, connecting to your existing MariaDB and InfluxDB instances. See [`unraid/README.md`](unraid/README.md) for full setup instructions.

| Container | Image | Address |
|-----------|-------|---------|
| gridmind-backend | `ghcr.io/richowen/gridmind-backend:latest` | `192.168.1.75:8009` |
| gridmind-frontend | `ghcr.io/richowen/gridmind-frontend:latest` | `192.168.1.76:3009` |

## Architecture

```
Browser :3009 (React + Tailwind)
    ↕ REST + WebSocket (nginx proxy)
Backend :8009 (FastAPI + APScheduler)
    ↕ SQL
MariaDB :3306 (external — existing Unraid instance)
    ↕ HTTP
InfluxDB :8086 (external — existing Unraid instance)
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

## First-Time Setup

1. Deploy containers via Unraid Docker GUI (see [`unraid/README.md`](unraid/README.md))
2. Alembic migrations run automatically on backend startup
3. Open `http://192.168.1.76:3009` and go to the **Settings** page to configure:
   - Home Assistant URL + token
   - Octopus Energy product/tariff/region codes
   - Battery capacity and limits
   - InfluxDB connection details
4. Click "Test HA Connection" to verify
5. Click "Refresh Prices" to fetch initial Agile prices
6. Automation starts immediately (every 5min optimization, every 1min immersion evaluation)

## Development

```bash
# Frontend dev server (requires node_modules)
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
│   └── alembic/           # Database migrations (001–007)
├── frontend/
│   └── src/
│       ├── api/           # API client functions
│       ├── components/    # React components
│       ├── hooks/         # Custom React hooks
│       ├── pages/         # Page components
│       └── types/         # TypeScript types
├── database/
│   └── seed_data.sql      # Reference seed data (handled by Alembic)
└── unraid/
    ├── gridmind-backend.xml   # Unraid container template
    ├── gridmind-frontend.xml  # Unraid container template
    ├── nginx.conf             # Frontend nginx config (copy to appdata)
    └── README.md              # Full Unraid deployment guide
```
