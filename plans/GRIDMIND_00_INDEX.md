# GridMind — Plan Index

**Project:** GridMind
**Purpose:** Modern self-contained solar battery intelligence system
**Replaces:** Battery Optimizer V2 (Node-RED hybrid)
**Deployment:** Docker on Unraid (192.168.1.2), browser-only access
**Repo:** This GitHub repo, reorganised in-place (legacy files → `legacy/`, new project → `gridmind/`)
**Codebase:** Entirely AI-coded — optimised for AI agent readability and editability

---

## Plan Documents

| File | Contents | Status |
|------|----------|--------|
| [`GRIDMIND_01_OVERVIEW.md`](GRIDMIND_01_OVERVIEW.md) | What changes, why, project structure, tech stack, AI coding guidelines | ✅ Ready |
| [`GRIDMIND_02_ARCHITECTURE.md`](GRIDMIND_02_ARCHITECTURE.md) | System architecture diagram, Docker deployment | ✅ Ready |
| [`GRIDMIND_03_BACKEND.md`](GRIDMIND_03_BACKEND.md) | Backend modules, scheduler, rules engine, action executor, WebSocket | ✅ Ready |
| [`GRIDMIND_04_DATABASE.md`](GRIDMIND_04_DATABASE.md) | Database schema (all tables), InfluxDB compatibility | ✅ Ready |
| [`GRIDMIND_05_FRONTEND.md`](GRIDMIND_05_FRONTEND.md) | Frontend pages, UI wireframes, component structure | ✅ Ready |
| [`GRIDMIND_SETTINGS_DESIGN.md`](GRIDMIND_SETTINGS_DESIGN.md) | Settings page detail, all config keys, optimizer bug fixes | ✅ Ready |

---

## Key Decisions Summary

| Decision | Choice | Reason |
|----------|--------|--------|
| Project name | GridMind | Emphasises intelligent grid/energy management |
| Codebase approach | AI-optimised small files | Entire codebase AI-coded; small focused files reduce token cost |
| Frontend | React 18 + TypeScript + Vite | Best ecosystem for dashboards |
| UI library | shadcn/ui + Tailwind CSS | Polished, accessible, no custom CSS |
| Charts | Recharts | React-native, responsive |
| Scheduler | APScheduler (in-process) | Replaces Node-RED flows, no extra broker needed |
| Database | MariaDB (existing) + Alembic migrations | Keep existing data, add new tables cleanly |
| Real-time | WebSocket (FastAPI native) | Push updates to browser |
| Immersion control | Temp targets + configurable rules engine | No fixed schedules; temp targets replace weekly time windows |
| Export price | Fixed SEG rate (configurable) | Currently 15p/kWh, not % of import |
| Load assumption | Configurable constant (kW) | Household load doesn't change based on battery/solar; constant is sufficient for optimizer |

---

## Hardware / Entity Reference

| Entity | ID | Purpose |
|--------|-----|---------|
| Battery SoC | `sensor.foxinverter_battery_soc` | State of charge % |
| Work Mode | `select.foxinverter_work_mode` | Force Charge / Self Use |
| Discharge Current | `number.foxinverter_max_discharge_current` | Amps |
| Solar Power | `sensor.pv_power_foxinverter` | Current generation kW |
| Solar Forecast Today | `sensor.solcast_pv_forecast_forecast_remaining_today` | kWh remaining |
| Solar Forecast 1hr | `sensor.solcast_pv_forecast_power_in_1_hour` | kW |
| Main Immersion Switch | `switch.immersion_switch` | On/Off |
| Lucy Immersion Switch | `switch.immersion_lucy_switch` | On/Off |
| Main Temp Sensor | `sensor.sonoff_1001e116e1_temperature` | °C |
| Lucy Temp Sensor | `sensor.t_h_sensor_with_external_probe_temperature_2` | °C |

---

## Implementation Phases

| Phase | Description | Milestone |
|-------|-------------|-----------|
| 1 | Backend scaffold + APScheduler + Action Executor | System runs autonomously without Node-RED |
| 2 | Database schema + Alembic migrations + Rules Engine | All data models in place |
| 3 | WebSocket + real-time state push | Browser gets live updates |
| 4 | React frontend — Dashboard + Price Chart | Basic UI working |
| 5 | React frontend — Immersion Manager | Rules editor + temp targets |
| 6 | React frontend — History + Controls + Settings | Full UI complete |
| 7 | Docker + deployment + Unraid template | Production ready |
