# GridMind — Modern Solar Battery Intelligence System

> **Project Name:** GridMind
> **Replaces:** Battery Optimizer V2 (Node-RED hybrid)

**Replaces:** Node-RED dashboard + automation flows  
**Goal:** Fully autonomous, self-contained Docker system with modern web GUI  
**Deployment:** Unraid server (192.168.1.2), browser-only access  
**Key Design Principle:** Zero hardcoded values — everything configurable through the UI, including immersion rules, thresholds, temperature targets, and which HA entities to use. Supports N immersion devices, not just main + lucy.
**AI Codebase:** Entirely AI-coded — small focused files, clear boundaries, minimal token cost. See `GRIDMIND_01_OVERVIEW.md` for AI coding guidelines.
**InfluxDB Compatibility:** All existing InfluxDB measurements and field names are preserved exactly — your Grafana dashboards will continue to work unchanged. New fields are additive only (temperature data added to `system_state` measurement).

---

## 0. Project Structure — GridMind

### 0.1 New Repository Layout

GridMind is built as a **clean new project** in a `gridmind/` directory. The existing legacy files (Node-RED flows, old docs, old backend) remain in the current workspace root as archive — they are not mixed into the new project.

```
gridmind/                          ← NEW clean project root
│
├── README.md                      ← GridMind documentation
├── docker-compose.yml             ← Single compose file for all services
├── .env.example                   ← Environment template
│
├── backend/                       ← Python FastAPI service
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/                   ← Database migrations (replaces manual SQL)
│   │   ├── env.py
│   │   └── versions/
│   │       ├── 001_initial_schema.py
│   │       ├── 002_immersion_devices.py
│   │       ├── 003_rules_engine.py
│   │       ├── 004_overrides.py
│   │       ├── 005_system_actions.py
│   │       └── 006_system_settings.py
│   └── app/
│       ├── __init__.py
│       ├── main.py                ← FastAPI app + lifespan (scheduler start)
│       ├── config.py              ← Pydantic settings (DB creds only)
│       ├── database.py            ← SQLAlchemy engine + session
│       │
│       ├── models/                ← SQLAlchemy ORM models (split by domain)
│       │   ├── __init__.py
│       │   ├── prices.py          ← ElectricityPrice, PriceAnalysis
│       │   ├── optimization.py    ← OptimizationResult, SystemState
│       │   ├── immersion.py       ← ImmersionDevice, SmartRule, TempTarget
│       │   ├── overrides.py       ← ManualOverride
│       │   ├── actions.py         ← SystemAction (audit log)
│       │   └── settings.py        ← SystemSetting
│       │
│       ├── schemas/               ← Pydantic request/response schemas
│       │   ├── __init__.py
│       │   ├── prices.py
│       │   ├── optimization.py
│       │   ├── immersion.py
│       │   ├── overrides.py
│       │   ├── settings.py
│       │   └── system.py
│       │
│       ├── routers/               ← Thin FastAPI route handlers (split by domain)
│       │   ├── __init__.py
│       │   ├── optimization.py    ← /api/v1/recommendation, /prices, /state
│       │   ├── immersion.py       ← /api/v1/immersions/* (devices, rules, targets)
│       │   ├── overrides.py       ← /api/v1/overrides/*
│       │   ├── history.py         ← /api/v1/history/*, /api/v1/actions
│       │   └── system.py         ← /api/v1/system/* (health, settings, control)
│       │
│       ├── services/              ← External integrations
│       │   ├── __init__.py
│       │   ├── home_assistant.py  ← HA REST API client
│       │   ├── octopus_energy.py  ← Octopus Agile API client
│       │   └── influxdb.py        ← InfluxDB write client
│       │
│       ├── core/                  ← Business logic
│       │   ├── __init__.py
│       │   ├── optimizer.py       ← LP optimization engine (from existing)
│       │   ├── rules_engine.py    ← Configurable immersion rules evaluator
│       │   ├── action_executor.py ← Applies decisions to HA
│       │   └── scheduler.py       ← APScheduler job definitions
│       │
│       └── websocket/             ← WebSocket management
│           ├── __init__.py
│           └── manager.py         ← Connection manager + broadcast
│
├── frontend/                      ← React + TypeScript + Vite
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx               ← React entry point
│       ├── App.tsx                ← Router + layout
│       │
│       ├── pages/                 ← Route-level components
│       │   ├── Dashboard.tsx
│       │   ├── Prices.tsx
│       │   ├── Immersions.tsx
│       │   ├── History.tsx
│       │   ├── Controls.tsx
│       │   └── Settings.tsx
│       │
│       ├── components/            ← Reusable UI components
│       │   ├── layout/
│       │   │   ├── Sidebar.tsx
│       │   │   └── Header.tsx
│       │   ├── dashboard/
│       │   │   ├── BatteryCard.tsx
│       │   │   ├── SolarCard.tsx
│       │   │   ├── PriceCard.tsx
│       │   │   └── ImmersionStatusCard.tsx
│       │   ├── charts/
│       │   │   ├── PriceChart.tsx
│       │   │   ├── SocChart.tsx
│       │   │   ├── SolarChart.tsx
│       │   │   └── TemperatureChart.tsx
│       │   ├── immersion/
│       │   │   ├── DeviceCard.tsx
│       │   │   ├── RulesEditor.tsx
│       │   │   └── TempTargetForm.tsx
│       │   └── ui/                ← shadcn/ui components
│       │
│       ├── hooks/                 ← Custom React hooks
│       │   ├── useWebSocket.ts    ← WebSocket connection + state
│       │   ├── useApi.ts          ← React Query wrappers
│       │   └── useLiveState.ts    ← Combined live state hook
│       │
│       ├── api/                   ← API client functions
│       │   ├── client.ts          ← Axios/fetch base client
│       │   ├── optimization.ts
│       │   ├── immersion.ts
│       │   ├── overrides.ts
│       │   └── history.ts
│       │
│       └── types/                 ← TypeScript type definitions
│           ├── api.ts             ← API response types
│           └── domain.ts          ← Domain model types
│
└── database/                      ← Database utilities
    ├── seed_data.sql              ← Initial immersion device data
    └── migrations/                ← Reference SQL (Alembic handles actual migrations)
```

### 0.2 What Happens to the Current Workspace

The current workspace (`Battery December 2025/`) becomes the **archive**. Nothing is deleted — it stays as reference. The new `gridmind/` directory is created alongside it (or as a new VS Code workspace).

```
Current workspace (archive - do not delete):
  Battery December 2025/
  ├── backend/          ← V2 backend (reference)
  ├── nodered/          ← Legacy flows (reference)
  ├── plans/            ← Architecture docs
  └── *.md              ← Documentation

New project (clean):
  gridmind/
  ├── backend/          ← V3 backend (GridMind)
  ├── frontend/         ← React UI (new)
  └── database/         ← Migration scripts
```

### 0.3 Key Structural Improvements Over V2

| V2 (current) | V3 GridMind |
|-------------|-------------|
| Single `api.py` (929 lines) | Split into `routers/` by domain |
| Single `models.py` | Split into `models/` by domain |
| No database migrations | Alembic migrations (versioned, repeatable) |
| Business logic in `api.py` | Separated into `core/` |
| No frontend | `frontend/` with React + TypeScript |
| Node-RED for automation | `core/scheduler.py` with APScheduler |

---

## 1. What Changes and Why

### Current Limitations (Node-RED)
| Problem | Impact |
|---------|--------|
| Node-RED dashboard is basic - limited charting | Poor data visibility |
| Flows are hard to maintain and debug | Fragile automation |
| No proper schedule editor UI | Manual JSON editing |
| No temperature-aware immersion control | Wasted energy |
| Node-RED is a separate dependency | Extra complexity |
| No history/analytics views | Can't review decisions |
| Hardcoded thresholds in Python code | Requires code changes to tune |
| Fixed to exactly 2 immersions | Not extensible |

### What Gets Eliminated
- All Node-RED flows (`nodered/` directory becomes legacy)
- Node-RED dependency entirely
- Manual flow editing for schedule changes
- All hardcoded thresholds (price limits, SOC limits, solar limits)

### What Gets Kept (Unchanged)
- Python FastAPI backend core
- LP optimization engine (`optimizer.py`)
- Home Assistant API client
- Octopus Energy API client
- InfluxDB client
- MariaDB database
- All existing API endpoints

---

## 2. New System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  UNRAID SERVER (192.168.1.2)                                        │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  FRONTEND CONTAINER (Nginx + React)  :3000                   │  │
│  │  • Dashboard - live battery/solar/price overview             │  │
│  │  • Price Chart - 48hr forecast with action overlay           │  │
│  │  • Immersion Manager - devices, rules, schedules, targets    │  │
│  │  • History - SOC/solar/price/temperature over time           │  │
│  │  • Controls - manual overrides, force charge/discharge       │  │
│  │  • Settings - battery config, entity IDs, system config      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                          ↕ REST + WebSocket                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  BACKEND CONTAINER (Python FastAPI)  :8000                   │  │
│  │                                                              │  │
│  │  ┌─────────────────────────────────────────────────────┐    │  │
│  │  │  APScheduler (replaces Node-RED automation)          │    │  │
│  │  │  • Every 5min: optimize → apply to HA               │    │  │
│  │  │  • Every 30min: refresh Octopus prices              │    │  │
│  │  │  • Every 1min: evaluate immersion rules + temp      │    │  │
│  │  │  • Every 5min: push state via WebSocket             │    │  │
│  │  └─────────────────────────────────────────────────────┘    │  │
│  │                                                              │  │
│  │  ┌─────────────────────────────────────────────────────┐    │  │
│  │  │  LP Optimizer (existing - unchanged)                 │    │  │
│  │  │  • 24-48hr price lookahead                          │    │  │
│  │  │  • Battery charge/discharge scheduling              │    │  │
│  │  └─────────────────────────────────────────────────────┘    │  │
│  │                                                              │  │
│  │  ┌─────────────────────────────────────────────────────┐    │  │
│  │  │  Configurable Rules Engine (NEW)                     │    │  │
│  │  │  • N immersion devices (not just main + lucy)       │    │  │
│  │  │  • Per-device: smart rules, schedules, temp targets │    │  │
│  │  │  • All thresholds stored in DB, editable via UI     │    │  │
│  │  │  • AND/OR condition logic per rule                  │    │  │
│  │  └─────────────────────────────────────────────────────┘    │  │
│  │                                                              │  │
│  │  ┌─────────────────────────────────────────────────────┐    │  │
│  │  │  Action Executor (NEW)                               │    │  │
│  │  │  • Applies optimizer recommendations to HA          │    │  │
│  │  │  • Logs every HA call to system_actions table       │    │  │
│  │  └─────────────────────────────────────────────────────┘    │  │
│  │                                                              │  │
│  │  ┌─────────────────────────────────────────────────────┐    │  │
│  │  │  WebSocket Manager (NEW)                             │    │  │
│  │  │  • Real-time state push to all connected browsers   │    │  │
│  │  └─────────────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                          ↕ SQL                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  MARIADB CONTAINER  :3306                                    │  │
│  │  • prices, recommendations, system_state (existing)         │  │
│  │  • immersion_devices (NEW - device registry)                │  │
│  │  • immersion_smart_rules (NEW - configurable rule engine)   │  │
│  │  • temperature_targets (NEW - temp-based goals)             │  │
│  │  • system_actions (NEW - audit log of HA calls)             │  │
│  │  • system_settings (NEW - all config in DB)                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                          ↕ HTTP                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  INFLUXDB CONTAINER  :8086 (existing, optional)              │  │
│  │  • Time-series data for history charts                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              ↕ HTTP REST
┌─────────────────────────────────────────────────────────────────────┐
│  HOME ASSISTANT VM (192.168.1.3:8123)                               │
│  • Fox Inverter entities (battery mode, discharge current, SOC)     │
│  • Solar power + Solcast forecast sensors                           │
│  • Immersion switches (main + lucy + any future devices)            │
│  • Temperature sensors (main + lucy probes)                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Frontend Design (React + TypeScript + Vite)

**Why React over alternatives:**
- Best charting ecosystem (Recharts)
- Component-based = easy to maintain
- TypeScript = type safety with the API
- Vite = fast builds, small Docker image
- shadcn/ui + Tailwind = polished, modern look

### 3.1 Page Structure

```
/                    → Dashboard (default)
/prices              → Price Chart + 48hr forecast
/immersions          → Immersion Manager (devices, rules, schedules, targets)
/history             → Historical data charts
/controls            → Manual overrides
/settings            → System configuration
```

### 3.2 Dashboard Page

```
┌─────────────────────────────────────────────────────────────┐
│  🔋 Battery Optimizer          ● Live    [18:42 GMT]        │
├──────────────┬──────────────┬──────────────┬───────────────┤
│  BATTERY     │  SOLAR       │  PRICE NOW   │  MODE         │
│  ████░░ 72%  │  ⚡ 4.2 kW   │  🟡 8.3p/kWh │  Self Use     │
│  Self Use    │  Today: 18kWh│  Next: 5.1p  │  50A discharge│
├──────────────┴──────────────┴──────────────┴───────────────┤
│  IMMERSION DEVICES                                          │
│  🔥 Main Hot Water: ON  │ 52°C │ Schedule: 18:00-20:00     │
│  🔥 Lucy's Tank:   OFF  │ 38°C │ Smart: waiting for price  │
├─────────────────────────────────────────────────────────────┤
│  PRICE CHART (next 12 hours - sparkline)                    │
│  [Colour-coded bar chart]                                   │
├─────────────────────────────────────────────────────────────┤
│  RECENT DECISIONS                                           │
│  18:40 - Self Use (50A) - Price 8.3p, SOC 72%             │
│  18:10 - Self Use (50A) - Price 9.1p, SOC 68%             │
│  17:40 - Force Charge - Price 2.1p, SOC 55%               │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Price Chart Page

```
┌─────────────────────────────────────────────────────────────┐
│  48-Hour Price Forecast                    [Refresh]        │
│                                                             │
│  [Full-width bar chart]                                     │
│  • Negative prices: Green bars (get paid!)                  │
│  • Cheap: Yellow bars (threshold configurable in settings)  │
│  • Normal: Blue bars                                        │
│  • Expensive: Red bars (threshold configurable)             │
│  • Overlay: planned charge/discharge actions                │
│  • Current time: vertical line                              │
│                                                             │
│  Stats: Min: -2.1p | Max: 38.4p | Avg: 14.2p              │
│  Negative periods: 3 | Cheap periods: 8                     │
└─────────────────────────────────────────────────────────────┘
```

### 3.4 Immersion Manager Page

```
┌─────────────────────────────────────────────────────────────┐
│  Immersion Control Manager                                  │
│                                                             │
│  DEVICES  [+ Add Device]                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 🔥 Main Hot Water Tank                    [Edit][⚙]  │  │
│  │    Switch: switch.immersion_switch                   │  │
│  │    Temp:   sensor.sonoff_1001e116e1_temperature      │  │
│  │    Status: ON | 52°C | Schedule active               │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 🔥 Lucy's Tank                            [Edit][⚙]  │  │
│  │    Switch: switch.immersion_lucy_switch              │  │
│  │    Temp:   sensor.t_h_sensor_with_external_probe_... │  │
│  │    Status: OFF | 38°C | Smart rule: waiting          │  │
│  └──────────────────────────────────────────────────────┘  │
│  [+ Add New Immersion Device]                               │
│                                                             │
│  ─── Configuring: Main Hot Water Tank ─────────────────── │
│                                                             │
│  TEMPERATURE TARGETS  [+ Add Target]                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Morning Hot Water                          [Edit][🗑] │  │
│  │ Ensure 30°C by 09:00 on Mon,Tue,Wed,Thu,Fri         │  │
│  │ Heating rate: 5°C/hr | Buffer: 30min                │  │
│  │ Status: ✅ 52°C (already at target)                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  SMART RULES  [+ Add Rule]                                  │
│  ┌─────┬────────────────────┬─────────────────┬─────────┐ │
│  │ Pri │ Rule Name          │ Conditions      │ Action  │ │
│  ├─────┼────────────────────┼─────────────────┼─────────┤ │
│  │  1  │ Negative Price     │ price < 0p      │ ON  ✅  │ │
│  │  2  │ Very Cheap + Full  │ price<2p AND    │ ON  ✅  │ │
│  │     │                    │ soc>95%         │         │ │
│  │  3  │ Solar Surplus      │ solar>5kW AND   │ ON  ✅  │ │
│  │     │                    │ soc>90%         │         │ │
│  │  4  │ Overheat Guard     │ temp > 70°C     │ OFF ✅  │ │
│  └─────┴────────────────────┴─────────────────┴─────────┘ │
│  [Edit] [Delete] [Reorder] for each rule                   │
└─────────────────────────────────────────────────────────────┘
```

### 3.5 History Page

```
┌─────────────────────────────────────────────────────────────┐
│  History & Analytics          [Last 24h] [7d] [30d]        │
│                                                             │
│  BATTERY SOC OVER TIME                                      │
│  [Line chart - SOC % vs time]                               │
│                                                             │
│  SOLAR GENERATION                                           │
│  [Area chart - kW vs time]                                  │
│                                                             │
│  ELECTRICITY PRICE                                          │
│  [Bar chart - p/kWh vs time, colour coded]                  │
│                                                             │
│  IMMERSION TEMPERATURE (all devices)                        │
│  [Line chart - °C vs time, one line per device]             │
│                                                             │
│  DECISIONS LOG                                              │
│  [Table: timestamp, mode, reason, SOC, price, solar]        │
└─────────────────────────────────────────────────────────────┘
```

### 3.6 Controls Page

```
┌─────────────────────────────────────────────────────────────┐
│  Manual Controls                                            │
│                                                             │
│  BATTERY MODE                                               │
│  [Force Charge] [Self Use] [Feed-in First]  ← toggle       │
│  Duration: [30min] [1hr] [2hr] [Until next auto]           │
│                                                             │
│  IMMERSION OVERRIDES (one section per registered device)    │
│  Main Hot Water:  [ON] [OFF] [Auto]  Duration: [2hr]       │
│  Lucy's Tank:     [ON] [OFF] [Auto]  Duration: [2hr]       │
│                                                             │
│  SYSTEM                                                     │
│  [Pause Automation]  [Resume Automation]                    │
│  [Refresh Prices Now]  [Force Optimize Now]                 │
│                                                             │
│  ACTIVE OVERRIDES                                           │
│  • Main Hot Water: ON until 20:30 (manual)  [Clear]        │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Backend Enhancements

### 4.1 New Python Modules

```
backend/app/
├── scheduler.py              # NEW - APScheduler integration
├── websocket_manager.py      # NEW - WebSocket connection manager
├── rules_engine.py           # NEW - Configurable immersion rules evaluator
├── action_executor.py        # NEW - Applies recommendations to HA
└── services/
    └── (existing unchanged)
```

### 4.2 APScheduler Jobs (replaces Node-RED flows)

```python
# Every 5 minutes: Main optimization loop
async def optimization_loop():
    state = await ha_client.get_system_state()
    prices = get_prices_from_db()
    result = optimizer.optimize(state, prices, settings)  # uses assumed_load_kw constant
    await action_executor.apply_battery(result)
    await websocket_manager.broadcast(state_update)

# Every 30 minutes: Price refresh
async def price_refresh():
    prices = await octopus_client.fetch_prices()
    store_prices_in_db(prices)
    await websocket_manager.broadcast(price_update)

# Every 1 minute: Immersion rules + temperature check
async def immersion_evaluation():
    devices = get_all_immersion_devices()
    system_state = get_current_system_state()
    for device in devices:
        decision = rules_engine.evaluate(device, system_state)
        await action_executor.apply_immersion(device, decision)
```

### 4.3 Configurable Rules Engine

```python
class RulesEngine:
    def evaluate(self, device: ImmersionDevice, state: SystemState) -> ImmersionDecision:
        """
        Evaluate all rules for a device in priority order.
        Returns the first matching rule's action.
        """
        # Check manual override first (always highest priority)
        if override := get_active_manual_override(device.id):
            return ImmersionDecision(action=override.desired_state, source="manual_override")
        
        # Check temperature targets
        for target in get_enabled_temp_targets(device.id):
            if self._temp_target_requires_heating(target, state):
                return ImmersionDecision(action=True, source="temperature_target",
                                        reason=f"Need {target.target_temp_c}°C by {target.target_time}")
        
        # Evaluate smart rules in priority order
        for rule in get_enabled_smart_rules(device.id):  # ordered by priority
            if self._rule_matches(rule, state):
                return ImmersionDecision(action=(rule.action == 'ON'), 
                                        source="smart_rule", reason=rule.rule_name)
        
        # Default: off
        return ImmersionDecision(action=False, source="default")
    
    def _rule_matches(self, rule: SmartRule, state: SystemState) -> bool:
        """Evaluate all conditions for a rule using AND/OR logic"""
        conditions = []
        
        if rule.price_enabled:
            conditions.append(self._compare(state.current_price, rule.price_operator, rule.price_threshold_pence))
        if rule.soc_enabled:
            conditions.append(self._compare(state.battery_soc, rule.soc_operator, rule.soc_threshold_percent))
        if rule.solar_enabled:
            conditions.append(self._compare(state.solar_power_kw, rule.solar_operator, rule.solar_threshold_kw))
        if rule.temp_enabled and state.device_temp is not None:
            conditions.append(self._compare(state.device_temp, rule.temp_operator, rule.temp_threshold_c))
        if rule.time_enabled:
            conditions.append(self._in_time_window(rule.time_start, rule.time_end))
        
        if not conditions:
            return False
        
        return all(conditions) if rule.logic_operator == 'AND' else any(conditions)
```

### 4.4 Action Executor (NEW - replaces Node-RED HA calls)

```python
class ActionExecutor:
    async def apply_battery(self, recommendation: dict):
        """Apply battery optimizer recommendation to Home Assistant"""
        await ha_client.set_battery_mode(recommendation["mode"])
        await ha_client.set_discharge_current(recommendation["discharge_current"])
        log_action("battery_mode", recommendation["mode"], "optimizer")
    
    async def apply_immersion(self, device: ImmersionDevice, decision: ImmersionDecision):
        """Apply immersion decision to Home Assistant"""
        current_state = await ha_client.get_switch_state(device.switch_entity_id)
        if current_state != decision.action:  # Only call HA if state changes
            await ha_client.set_switch(device.switch_entity_id, decision.action)
            log_action("immersion", device.name, decision.action, decision.source, decision.reason)
```

### 4.5 WebSocket Endpoint

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Send current state immediately on connect
    await websocket.send_json(get_current_state())
    try:
        while True:
            await asyncio.sleep(30)  # Keep alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

---

## 5. Database Schema (New Tables)

### 5.1 Immersion Device Registry

```sql
CREATE TABLE immersion_devices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    switch_entity_id VARCHAR(100) NOT NULL,
    temp_sensor_entity_id VARCHAR(100),
    is_enabled BOOLEAN DEFAULT TRUE,
    sort_order INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Seed data for existing setup
INSERT INTO immersion_devices VALUES
(1, 'main', 'Main Hot Water Tank', 'switch.immersion_switch', 
 'sensor.sonoff_1001e116e1_temperature', TRUE, 1, NOW(), NOW()),
(2, 'lucy', "Lucy's Tank", 'switch.immersion_lucy_switch',
 'sensor.t_h_sensor_with_external_probe_temperature_2', TRUE, 2, NOW(), NOW());
```

### 5.2 Smart Rules Engine

```sql
CREATE TABLE immersion_smart_rules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    immersion_id INT NOT NULL REFERENCES immersion_devices(id),
    rule_name VARCHAR(100) NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    priority INT DEFAULT 10,
    action VARCHAR(10) NOT NULL,             -- 'ON' or 'OFF'
    logic_operator VARCHAR(3) DEFAULT 'AND', -- 'AND' or 'OR'
    
    -- Price condition
    price_enabled BOOLEAN DEFAULT FALSE,
    price_operator VARCHAR(5),               -- '<', '<=', '>', '>='
    price_threshold_pence FLOAT,
    
    -- Battery SOC condition
    soc_enabled BOOLEAN DEFAULT FALSE,
    soc_operator VARCHAR(5),
    soc_threshold_percent FLOAT,
    
    -- Solar power condition
    solar_enabled BOOLEAN DEFAULT FALSE,
    solar_operator VARCHAR(5),
    solar_threshold_kw FLOAT,
    
    -- Temperature condition (device's own sensor)
    temp_enabled BOOLEAN DEFAULT FALSE,
    temp_operator VARCHAR(5),
    temp_threshold_c FLOAT,
    
    -- Time of day condition
    time_enabled BOOLEAN DEFAULT FALSE,
    time_start TIME,
    time_end TIME,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_device_priority (immersion_id, is_enabled, priority)
);
```

### 5.3 Temperature Targets

```sql
CREATE TABLE temperature_targets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    immersion_id INT NOT NULL REFERENCES immersion_devices(id),
    target_name VARCHAR(100) NOT NULL,
    target_temp_c FLOAT NOT NULL,
    target_time TIME NOT NULL,
    days_of_week VARCHAR(20) NOT NULL,       -- e.g. '0,1,2,3,4'
    heating_rate_c_per_hour FLOAT DEFAULT 5.0,
    buffer_minutes INT DEFAULT 30,
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 5.4 System Actions Audit Log

```sql
CREATE TABLE system_actions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    timestamp DATETIME NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    old_value VARCHAR(100),
    new_value VARCHAR(100) NOT NULL,
    source VARCHAR(50) NOT NULL,             -- 'optimizer', 'schedule', 'manual', 'temperature', 'smart_rule'
    reason TEXT,
    success BOOLEAN DEFAULT TRUE,
    INDEX idx_timestamp (timestamp),
    INDEX idx_action_type (action_type)
);
```

---

## 6. Immersion Control Priority System

Priority is evaluated in this order (all configurable, no hardcoded values):

```
PRIORITY 1: Manual Override
    └─ User explicitly set via UI
    └─ Expires after user-configured duration
    └─ Stored in manual_overrides table

PRIORITY 2: Temperature Target
    └─ "Ensure X°C by Y time on these days"
    └─ Heating rate and buffer are configurable per device
    └─ Turns on as needed to meet target
    └─ Stored in temperature_targets table

PRIORITY 3+: Smart Rules (each has its own priority number)
    └─ Configurable conditions: price, SOC, solar, temp, time
    └─ AND/OR logic between conditions
    └─ Action: ON or OFF
    └─ Stored in immersion_smart_rules table
    └─ Examples (all configurable, not hardcoded):
       - "Negative Price": price < 0p → ON
       - "Very Cheap + Full": price < 2p AND soc > 95% → ON
       - "Solar Surplus": solar > 5kW AND soc > 90% → ON
       - "Overheat Guard": temp > 70°C → OFF
       - "Night Lockout": time 23:00-05:00 → OFF

DEFAULT: OFF
```

> **Note:** Fixed weekly schedules have been removed. Temperature targets ("ensure X°C by Y time") are strictly more intelligent — they account for current temperature and heating rate rather than blindly running during fixed time windows.

---

## 7. New API Endpoints

### Immersion Device Management
```
GET    /api/v1/immersions/devices              - List all devices
POST   /api/v1/immersions/devices              - Add new device
PUT    /api/v1/immersions/devices/{id}         - Update device
DELETE /api/v1/immersions/devices/{id}         - Remove device
GET    /api/v1/immersions/devices/{id}/status  - Current status + temp
```

### Smart Rules
```
GET    /api/v1/immersions/{id}/rules           - List rules for device
POST   /api/v1/immersions/{id}/rules           - Add rule
PUT    /api/v1/immersions/{id}/rules/{rule_id} - Update rule
DELETE /api/v1/immersions/{id}/rules/{rule_id} - Delete rule
POST   /api/v1/immersions/{id}/rules/reorder   - Reorder priorities
```

### Temperature Targets
```
GET    /api/v1/immersions/{id}/targets         - List targets
POST   /api/v1/immersions/{id}/targets         - Add target
PUT    /api/v1/immersions/{id}/targets/{tid}   - Update target
DELETE /api/v1/immersions/{id}/targets/{tid}   - Remove target
```

### System Actions Log
```
GET    /api/v1/actions                         - Recent actions (paginated)
GET    /api/v1/actions?entity_id=X&hours=24    - Filtered actions
```

---

## 8. Docker Deployment

### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=mariadb
      - INFLUX_URL=http://influxdb:8086
    depends_on:
      - mariadb
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

  mariadb:
    image: mariadb:10.11
    ports:
      - "3306:3306"
    volumes:
      - mariadb_data:/var/lib/mysql
    restart: unless-stopped

  influxdb:
    image: influxdb:2.7
    ports:
      - "8086:8086"
    volumes:
      - influxdb_data:/var/lib/influxdb2
    restart: unless-stopped

volumes:
  mariadb_data:
  influxdb_data:
```

### Frontend Dockerfile

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### Nginx Config

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location /api/ {
        proxy_pass http://backend:8000;
    }

    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

---

## 9. InfluxDB Compatibility (Grafana Dashboard Preservation)

### 9.1 Existing Measurements — Preserved Exactly

All existing measurements, tags, and field names are kept **unchanged**. The V3 system writes to the same bucket (`battery-optimizer`) with identical schema. Your Grafana dashboards will continue to work without any changes.

| Measurement | Tags | Fields | V3 Status |
|-------------|------|--------|-----------|
| `electricity_price` | `classification`, `is_negative` | `price_pence`, `price_pounds` | ✅ Unchanged |
| `price_analysis` | `data_type` | `min_price`, `max_price`, `mean_price`, `median_price`, `cheap_threshold`, `expensive_threshold`, `negative_count`, `cheap_count`, `expensive_count`, `total_periods` | ✅ Unchanged |
| `battery_decision` | `mode`, `optimization_status` | `discharge_current`, `expected_soc`, `immersion_main`, `immersion_lucy`, `optimization_time_ms` | ✅ Unchanged |
| `system_state` | `battery_mode` | `battery_soc`, `solar_power_kw`, `solar_forecast_today_kwh`, `discharge_current`, `immersion_main_on`, `immersion_lucy_on`, `current_price_pence` | ✅ Unchanged |

### 9.2 New Fields Added (Additive Only — Won't Break Existing Queries)

**`system_state` measurement gets new optional fields** (only written when temperature data is available):
```
temp_main_c              - Main immersion temperature in °C
temp_lucy_c              - Lucy's tank temperature in °C
immersion_main_source    - 'manual_override', 'schedule', 'smart_rule', 'temperature_target', 'default'
immersion_lucy_source    - same as above
```

**New measurement: `immersion_action`** (audit log, new — won't affect existing queries):
```
Tags:   device_name, action, source
Fields: success (bool), reason (string)
```

### 9.3 Implementation Rule for influxdb_client.py

The [`influxdb_client.py`](backend/app/services/influxdb_client.py) file will be modified with **additive changes only**:
- `write_prices()` — **no changes**
- `write_price_analysis()` — **no changes**
- `write_optimization_result()` — **no changes**
- `write_system_state()` — existing fields unchanged, new optional temperature fields appended
- `write_immersion_action()` — **new method added** for audit log

---

## 10. New HA Entity IDs to Add to Config

```env
# Temperature sensors — stored in immersion_devices table, editable via UI
# (not hardcoded in .env — these are the seed values for initial setup)
HA_ENTITY_TEMP_MAIN=sensor.sonoff_1001e116e1_temperature
HA_ENTITY_TEMP_LUCY=sensor.t_h_sensor_with_external_probe_temperature_2
```

These will be stored in the `immersion_devices` table and editable via the Settings UI — not hardcoded in `.env`.

---

## 10. Implementation Phases

### Phase 1: Backend Scheduler + Action Executor
- Add APScheduler to backend
- Add `action_executor.py` (apply recommendations to HA)
- Add `scheduler.py` (5min/30min/1min jobs)
- Add temperature sensor reading to HA client
- **Milestone:** System runs autonomously without Node-RED

### Phase 2: Database + Rules Engine
- Create new DB tables (devices, smart_rules, temperature_targets, system_actions, system_settings)
- Add `rules_engine.py` with configurable condition evaluation
- Seed initial device data (main + lucy)
- Add all new API endpoints (CRUD for devices, rules, targets)

### Phase 3: WebSocket
- Add `websocket_manager.py`
- Add `/ws` WebSocket endpoint
- Integrate with scheduler to push updates on state change

### Phase 4: React Frontend - Core + Dashboard
- Setup Vite + React + TypeScript project
- Install: Tailwind CSS, shadcn/ui, Recharts, React Router, React Query
- Dashboard page (live data via WebSocket)
- Price chart page

### Phase 5: React Frontend - Immersion Manager
- Device registry UI (add/edit/remove devices)
- Smart rules editor (add conditions, AND/OR logic, priority drag-reorder)
- Temperature target configuration

### Phase 6: React Frontend - History + Controls
- History charts (SOC, solar, price, temperature over time)
- Manual controls page (battery mode, immersion overrides)
- Settings page (battery config, system settings)

### Phase 7: Docker + Deployment
- Frontend Dockerfile + Nginx config
- Update docker-compose.yml
- Update Unraid template
- Migration guide from Node-RED

---

## 11. Technology Stack Summary

| Layer | Technology | Reason |
|-------|-----------|--------|
| Backend API | Python FastAPI (existing) | Already solid, keep it |
| Scheduler | APScheduler 3.x | Mature, async-compatible, in-process |
| LP Optimizer | PuLP + CBC (existing) | Keep unchanged |
| Rules Engine | Python (new module) | Evaluates DB-stored rules |
| Database | MariaDB (existing) | Keep, add new tables |
| Time-series | InfluxDB (existing) | Keep for history charts |
| Frontend | React 18 + TypeScript | Best ecosystem for dashboards |
| Build tool | Vite | Fast, modern |
| UI Components | shadcn/ui + Tailwind CSS | Polished, accessible |
| Charts | Recharts | React-native, responsive |
| Real-time | WebSocket (FastAPI native) | Simple, no extra deps |
| Frontend server | Nginx | Lightweight, handles SPA routing + API proxy |
| Container | Docker + docker-compose | Existing deployment method |

---

## 12. Access URLs (after deployment)

| Service | URL | Purpose |
|---------|-----|---------|
| Web UI | http://192.168.1.2:3000 | Main interface |
| API | http://192.168.1.2:8000 | REST API |
| API Docs | http://192.168.1.2:8000/docs | Swagger UI |
| InfluxDB | http://192.168.1.2:8086 | Time-series DB |

---

## 13. Migration Path

1. **Keep Node-RED running** during Phase 1-3 development
2. **Phase 1 complete**: Python scheduler takes over automation (disable Node-RED flows)
3. **Phase 4-6 complete**: React UI available at :3000
4. **Cutover**: Stop Node-RED, use new system exclusively
5. **Archive**: Keep `nodered/` directory as reference

---

## 14. Key Design Decisions

### Why configurable rules engine over hardcoded thresholds?
- Tuning the system (e.g. "turn on at 3p not 2p") requires no code changes
- Different immersion tanks may need different rules (one is bigger, heats slower)
- Future-proof: add new conditions (e.g. grid carbon intensity) without code changes
- User can experiment with rules and see results in history

### Why N immersion devices instead of fixed main + lucy?
- Adding a third immersion (e.g. garage) requires no code changes
- Each device has its own rules, schedules, and temperature targets
- Devices can be enabled/disabled without removing configuration

### Why React over Streamlit/Dash?
- React gives full control over the UI and real-time WebSocket updates
- Recharts provides beautiful, responsive charts out of the box
- Component-based architecture aligns with AI-optimised small-file approach

### Why APScheduler over Celery?
- Celery requires Redis/RabbitMQ as a broker — extra complexity
- APScheduler runs in-process with FastAPI — simpler deployment
- The job frequency (every 1-5 minutes) is well within APScheduler's capabilities

---

*Plan created: March 2026*  
*Status: Awaiting approval*
