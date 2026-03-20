# GridMind V1 — Code Audit: Issues, Out-of-Scope Code & Waste

Audited: 2026-03-20  
Auditor: Code Skeptic mode  
Status: **Pending fixes**

---

## 🔴 CRITICAL — Bugs / Data Integrity

### Issue 1 — Mixed `datetime.now()` vs `datetime.utcnow()` — timestamp corruption in BST
**Severity:** Critical  
**Files:**
- `backend/app/core/scheduler.py` lines 100, 146, 148, 163
- `backend/app/routers/history.py` lines 24, 41, 59, 83
- `backend/app/core/action_executor.py` line 31

**Problem:**  
The code explicitly comments *"DB stores naive UTC datetimes — use `utcnow()` for comparisons"* at line 100, then immediately uses `datetime.now()` (local time) at lines 146, 148, 163 for writing `OptimizationResult` and `SystemState` timestamps. The history router also uses `datetime.now()` for all `since` calculations. In BST (UTC+1) every record is timestamped 1 hour wrong and history queries return wrong windows.

**Fix:**  
Replace all `datetime.now()` with `datetime.utcnow()` in DB write/query paths, or adopt timezone-aware datetimes throughout using `datetime.now(timezone.utc)`.

---

### Issue 2 — Override expiry check uses local time vs UTC DB — overrides never clear correctly
**Severity:** Critical  
**Files:**
- `backend/app/core/scheduler.py` line 305
- `backend/app/core/rules_engine.py` line 45

**Problem:**  
```python
ManualOverride.expires_at > datetime.now()
```
`expires_at` is stored as naive UTC (from the DB), but `datetime.now()` is local time. In BST, overrides expire 1 hour late. The `rules_engine.py` also uses `datetime.now()` for the remaining-minutes calculation, compounding the error.

**Fix:**  
Use `datetime.utcnow()` for all comparisons against DB-stored naive UTC datetimes.

---

### Issue 3 — `next_action_time` column is never written — always null
**Severity:** Critical (dead schema)  
**Files:**
- `backend/app/models/optimization.py` line 22
- `backend/app/core/scheduler.py` lines 145–156
- `frontend/src/types/api.ts` line 34

**Problem:**  
The `OptimizationResult` model has a `next_action_time` column. The scheduler never sets it. The frontend type declares `next_action_time: string | null`. It is always `null`.

**Fix:**  
Either populate `next_action_time` with the next scheduled run time, or drop the column from the model, migration, and frontend type.

---

## 🟠 HIGH — Out-of-Scope / Hardcoded Remnants

### Issue 4 — `system_states` table has hardcoded device columns `immersion_main_on` / `immersion_lucy_on`
**Severity:** High — violates "N immersion devices" design principle  
**Files:**
- `backend/alembic/versions/001_initial_schema.py` lines 57–58
- `backend/app/models/optimization.py` lines 39–40
- `backend/app/services/influxdb.py` lines 72–73
- `frontend/src/types/api.ts` lines 47–48

**Problem:**  
The README states *"N immersion devices — not fixed to 2"*, but the `system_states` table has `immersion_main_on` and `immersion_lucy_on` as fixed boolean columns. The InfluxDB writer also references these by name. These are never populated by the scheduler. They are dead columns that contradict the N-device design.

**Fix:**  
Remove `immersion_main_on` and `immersion_lucy_on` from `system_states`. If immersion state logging is needed, write a separate `immersion_states` measurement to InfluxDB keyed by device name.

---

### Issue 5 — `influxdb.py` references `temp_main_c` / `temp_lucy_c` by hardcoded name
**Severity:** High — dead code + hardcoded device names  
**File:** `backend/app/services/influxdb.py` lines 77–80

**Problem:**  
```python
if state.get("temp_main_c") is not None:
    point = point.field("temp_main_c", state["temp_main_c"])
if state.get("temp_lucy_c") is not None:
    point = point.field("temp_lucy_c", state["temp_lucy_c"])
```
These keys are never passed by the scheduler's `write_system_state` call. Dead code that also hardcodes device names.

**Fix:**  
Remove these lines. Temperature logging should be done per-device in `write_immersion_action` or a new `write_immersion_state` method.

---

### Issue 6 — `seed_data.sql` hardcodes device IDs 1 and 2
**Severity:** High  
**File:** `database/seed_data.sql` lines 13–35

**Problem:**  
All smart rules use `immersion_id = 1` with `WHERE NOT EXISTS` guards. If the DB is seeded in a different order, rules attach to the wrong device silently.

**Fix:**  
Use a subquery to look up the device by `name` rather than hardcoding `immersion_id = 1`:
```sql
SELECT id FROM immersion_devices WHERE name = 'main'
```

---

### Issue 7 — `ha_entity_solar_forecast_1hr` setting and `solar_forecast_next_hour_kw` column are never used
**Severity:** High — dead setting + dead column  
**Files:**
- `backend/alembic/versions/006_system_settings.py` line 51
- `backend/app/models/optimization.py` line 37
- `backend/app/services/home_assistant.py` (no `get_solar_forecast_1hr` method exists)

**Problem:**  
The setting is seeded and visible in the Settings UI. The column exists in `system_states`. Neither is ever read or written. Users who configure this setting will see no effect.

**Fix:**  
Either implement `get_solar_forecast_1hr()` in the HA client and write it to `SystemState`, or remove the setting and column.

---

### Issue 8 — `optimization_interval_minutes` and `price_refresh_interval_minutes` settings are ignored
**Severity:** High — misleading UI  
**Files:**
- `backend/alembic/versions/006_system_settings.py` lines 59–60
- `backend/app/core/scheduler.py` lines 72, 217

**Problem:**  
The scheduler hardcodes `minutes=5` and `minutes=30` in the `@scheduler.scheduled_job` decorators. The DB settings for these intervals exist and are editable in the Settings UI — but changing them has zero effect.

**Fix:**  
Either read these settings at startup and configure the scheduler dynamically, or remove the settings from the DB and document the intervals as fixed.

---

### Issue 9 — `octopus_region` setting is seeded but never used in the API URL
**Severity:** High — dead setting  
**Files:**
- `backend/alembic/versions/006_system_settings.py` line 54
- `backend/app/services/octopus_energy.py` line 33

**Problem:**  
```python
return f"{OCTOPUS_API_BASE}/products/{product}/electricity-tariffs/{tariff}/standard-unit-rates/"
```
The region code is in the DB but not interpolated into the URL. The tariff code already encodes the region, so this is redundant — but it's still a dead setting that misleads users.

**Fix:**  
Remove the `octopus_region` setting, or use it to auto-construct the tariff code so users only need to enter the region.

---

## 🟡 MEDIUM — Waste / Structural Issues

### Issue 10 — `InfluxDBClient` creates a new HTTP client on every write call
**Severity:** Medium — performance waste  
**File:** `backend/app/services/influxdb.py` lines 16–24, 37, 64, 94

**Problem:**  
`_get_client()` is called inside every `write_*` method, creating and destroying an HTTP connection pool on every 5-minute tick.

**Fix:**  
Cache the client as an instance attribute. Recreate only when settings change (hook into `invalidate_settings_cache`).

---

### Issue 11 — `HomeAssistantClient` creates a new `httpx.AsyncClient` on every call
**Severity:** Medium — performance waste  
**File:** `backend/app/services/home_assistant.py` lines 28, 91, 108, 124

**Problem:**  
Every HA call opens and closes a new `httpx.AsyncClient`. The optimization loop makes 6 HA reads + 2 writes per 5-minute cycle = 8 connection setups per cycle.

**Fix:**  
Use a shared `httpx.AsyncClient` instance (created in `__init__` or as a module-level singleton) with connection pooling.

---

### Issue 12 — `action_executor.py` fetches the same setting key twice
**Severity:** Medium — minor waste  
**File:** `backend/app/core/action_executor.py` lines 69, 73

**Problem:**  
`ha_entity_discharge_current` is fetched via `get_setting()` twice in the same method call (once to read current state, once to log the action).

**Fix:**  
Assign to a local variable once and reuse it.

---

### Issue 13 — `_log_action` opens its own DB session while caller already has one
**Severity:** Medium — unnecessary DB connections  
**File:** `backend/app/core/action_executor.py` line 28

**Problem:**  
`_log_action` is a standalone function that opens its own `SessionLocal()`. The caller (scheduler) already has a session context. This means 2 DB connections are open simultaneously during action logging.

**Fix:**  
Pass the existing `db` session into `_log_action` as a parameter.

---

### Issue 14 — `optimization_loop` opens two separate DB sessions
**Severity:** Medium — unnecessary DB connections  
**File:** `backend/app/core/scheduler.py` lines 98–113, 143–170

**Problem:**  
The first session reads prices (lines 98–113), closes, then a second session writes results (lines 143–170). Combined with `_log_action` opening a third session, a single optimization cycle opens 3 DB connections.

**Fix:**  
Use a single session for the entire optimization loop body.

---

### Issue 15 — `DAY_NAMES` in `domain.ts` uses 0=Mon but `Immersions.tsx` uses 0=Sun
**Severity:** Medium — inconsistency / latent bug  
**Files:**
- `frontend/src/types/domain.ts` lines 28–36
- `frontend/src/pages/Immersions.tsx` line 288

**Problem:**  
`domain.ts` maps 0→Mon (Python `weekday()` convention). `Immersions.tsx` uses its own local `DAY_LABELS = ['Sun', 'Mon', ...]` (JS `getDay()` convention). The `DAY_NAMES` export in `domain.ts` is never used in `Immersions.tsx` — it's dead code that would produce wrong day labels if used.

**Fix:**  
Pick one convention (recommend Python's 0=Mon to match the backend `days_of_week` storage), update `DAY_LABELS` in `Immersions.tsx` to match, and delete the duplicate definition.

---

### Issue 16 — `classifyPrice()` in `domain.ts` duplicates backend logic with hardcoded thresholds
**Severity:** Medium — duplication + stale data risk  
**Files:**
- `frontend/src/types/domain.ts` lines 55–65
- `backend/app/services/octopus_energy.py` lines 77–84
- `backend/app/core/scheduler.py` lines 175–185

**Problem:**  
Price classification is implemented in three places. The frontend version uses hardcoded defaults (`negThreshold=0, cheapThreshold=10, expThreshold=25`) that may not match the DB settings. If a user changes thresholds in Settings, the frontend sparkline colours won't update.

**Fix:**  
Remove `classifyPrice()` from `domain.ts`. Use the `classification` field already returned by the backend on every price record.

---

### Issue 17 — `CORS allow_origins=["*"]` in production
**Severity:** Medium — security  
**File:** `backend/app/main.py` line 37

**Problem:**  
Wildcard CORS means any website can make authenticated requests to the backend if the user's browser has a session.

**Fix:**  
Set `allow_origins` to the frontend origin (e.g. `["http://192.168.1.76:3009"]`) or read it from an environment variable.

---

### Issue 18 — WebSocket initial state on connect is incomplete
**Severity:** Medium — stale UI on first connect  
**File:** `backend/app/websocket/manager.py` lines 53–63

**Problem:**  
The initial state sent on WebSocket connect omits `battery_mode`, `solar_forecast_today_kwh`, `price_classification`, `battery_discharge_current`, and `live_charge_rate_kw`. A freshly connected browser shows null values for these until the next 5-minute optimization tick.

**Fix:**  
Expand the initial state payload to include all fields that the `optimization_result` broadcast includes. Consider also reading the latest `SystemState` row to populate `battery_mode`.

---

### Issue 19 — `SystemState` fields written by scheduler are a subset of the model columns
**Severity:** Medium — dead columns  
**Files:**
- `backend/app/models/optimization.py` lines 34–40
- `backend/app/core/scheduler.py` lines 159–166

**Problem:**  
`battery_discharge_current`, `solar_forecast_next_hour_kw`, `immersion_main_on`, `immersion_lucy_on` are in the `SystemState` model and schema but the scheduler's `state_record` never sets them. They are always `null` in the DB.

**Fix:**  
Either populate these fields or remove them from the model, migration, and schema.

---

## 🔵 LOW — Minor / Style

### Issue 20 — `import json` in `system.py` is unused
**Severity:** Low  
**File:** `backend/app/routers/system.py` line 3

**Fix:** Remove the import.

---

### Issue 21 — `force_charge_threshold_kw` reused as Force Discharge threshold; magic `0.05` hardcoded
**Severity:** Low  
**File:** `backend/app/core/optimizer.py` lines 246–249

**Problem:**  
The comment acknowledges this is a shortcut. The `export_0 > 0.05` guard is a magic number with no setting.

**Fix:**  
Add a `force_discharge_threshold_kw` setting (can default to same value). Add `force_discharge_export_min_kw` setting for the `0.05` guard.

---

### Issue 22 — Max discharge current sent to inverter even in Self Use mode
**Severity:** Low  
**File:** `backend/app/core/optimizer.py` lines 260–268

**Problem:**  
`recommended_discharge_current` is always set to `max_discharge_amps` regardless of mode. In Self Use mode, the inverter manages its own discharge — sending max current is unnecessary.

**Fix:**  
Only set discharge current when mode is `Force Discharge`. In `Self Use` and `Force Charge`, leave the current at its existing value (or set a sensible default).

---

### Issue 23 — `get_setting_bool()` defined but never called
**Severity:** Low — dead utility  
**File:** `backend/app/core/settings_cache.py` lines 68–71

**Problem:**  
`influxdb.py` does its own inline boolean parse instead of using this helper.

**Fix:**  
Use `get_setting_bool("influx_enabled", True)` in `influxdb.py` and remove the inline parse.

---

### Issue 24 — `send` function exported from `useWebSocket` but never called
**Severity:** Low — dead export  
**Files:**
- `frontend/src/hooks/useWebSocket.ts` lines 54–58
- `backend/app/websocket/manager.py` lines 72–73

**Problem:**  
`send` is exported but no component calls it. The only server-side handler for received messages is the `"refresh"` → `"pong"` echo, which is also never triggered.

**Fix:**  
Remove the `send` export and the `"refresh"` handler, or implement a use case for client-to-server messaging.

---

## Priority Fix Order

| Priority | Issue # | Description |
|----------|---------|-------------|
| 1 | 1, 2 | Replace `datetime.now()` with `datetime.utcnow()` in all DB paths |
| 2 | 8 | Read interval settings from DB at startup or remove dead settings |
| 3 | 4, 5, 19 | Remove hardcoded `immersion_main_on/lucy_on` and unpopulated `SystemState` columns |
| 4 | 7 | Implement or remove `solar_forecast_next_hour_kw` / `ha_entity_solar_forecast_1hr` |
| 5 | 9 | Remove or use `octopus_region` setting |
| 6 | 3 | Populate or drop `next_action_time` |
| 7 | 10, 11 | Reuse HTTP clients (InfluxDB, httpx) |
| 8 | 13, 14 | Consolidate DB sessions in optimization loop |
| 9 | 15, 16 | Fix day-of-week inconsistency; remove duplicate `classifyPrice()` |
| 10 | 17 | Lock CORS to frontend origin |
| 11 | 18 | Complete initial WebSocket state payload |
| 12 | 20–24 | Low-severity cleanup (unused imports, dead exports, magic numbers) |
