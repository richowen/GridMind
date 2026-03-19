# GridMind — Backend Design

## Implementation Notes

### Settings Caching
Settings are read from the DB on every scheduler cycle. To avoid excessive DB queries, cache settings in memory:

```python
# core/settings_cache.py
# Purpose: In-memory cache for system_settings with 60-second TTL

_cache: dict = {}
_cache_time: float = 0.0
CACHE_TTL = 60.0  # seconds

def get_settings() -> dict:
    global _cache, _cache_time
    if time.time() - _cache_time > CACHE_TTL:
        _cache = load_settings_from_db()
        _cache_time = time.time()
    return _cache

def invalidate_settings_cache():
    """Call this after PUT /api/v1/settings"""
    global _cache_time
    _cache_time = 0.0
```

### Scheduler Error Handling
Every scheduler job must wrap its body in try/except to prevent HA unavailability from crashing the scheduler:

```python
@scheduler.scheduled_job('interval', minutes=5)
async def optimization_loop():
    try:
        # ... job body
    except Exception as e:
        logger.error(f"optimization_loop failed: {e}")
        # Don't re-raise — let the scheduler continue
```

### LP Optimizer Thread Safety
PuLP/CBC runs synchronously. Run it in a thread pool to avoid blocking the async event loop:

```python
import asyncio
result = await asyncio.get_event_loop().run_in_executor(
    None, optimizer.optimize, state, prices, settings
)
```

---

## APScheduler Jobs (replaces Node-RED flows)

```python
# core/scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# Every 5 minutes: Main optimization loop
@scheduler.scheduled_job('interval', minutes=5)
async def optimization_loop():
    """
    1. Get current system state from HA (SOC, solar, mode)
    2. Get prices from DB
    3. Run LP optimization (uses configurable constant load assumption)
    4. Apply battery recommendation to HA
    5. Store result in DB + InfluxDB
    6. Push update via WebSocket
    """
    settings = get_settings()
    state = await ha_client.get_system_state()
    prices = get_prices_from_db()
    result = optimizer.optimize(state, prices, settings)
    await action_executor.apply_battery(result)
    await websocket_manager.broadcast_state(result)

# Every 30 minutes: Price refresh
@scheduler.scheduled_job('interval', minutes=30)
async def price_refresh():
    """Fetch latest Agile prices from Octopus API"""
    prices = await octopus_client.fetch_prices()
    store_prices_in_db(prices)
    if influx_client.enabled:
        influx_client.write_prices(prices)
    await websocket_manager.broadcast_prices(prices)

# Every 1 minute: Immersion rules + temperature evaluation
@scheduler.scheduled_job('interval', minutes=1)
async def immersion_evaluation():
    """
    For each enabled immersion device:
    1. Get current temperature from HA
    2. Evaluate rules in priority order
    3. Apply decision to HA (only if state changes)
    4. Log action
    """
    devices = get_enabled_devices()
    system_state = get_current_system_state()
    for device in devices:
        temp = await ha_client.get_temperature(device.temp_sensor_entity_id)
        decision = rules_engine.evaluate(device, system_state, temp)
        await action_executor.apply_immersion(device, decision)
```

---

## Configurable Rules Engine

```python
# core/rules_engine.py

class RulesEngine:
    def evaluate(
        self,
        device: ImmersionDevice,
        state: SystemState,
        current_temp: Optional[float]
    ) -> ImmersionDecision:
        """
        Evaluate all rules for a device in priority order.
        Returns the first matching rule's action.
        """
        
        # PRIORITY 1: Manual Override (always wins)
        if override := get_active_manual_override(device.id):
            return ImmersionDecision(
                action=override.desired_state,
                source="manual_override",
                reason=f"Manual override active ({override.time_remaining_minutes}min remaining)"
            )
        
        # PRIORITY 2: Temperature Target
        for target in get_enabled_temp_targets(device.id):
            if self._temp_target_requires_heating(target, current_temp):
                return ImmersionDecision(
                    action=True,
                    source="temperature_target",
                    reason=f"Need {target.target_temp_c}°C by {target.target_time}"
                )
        
        # PRIORITY 3+: Smart Rules (ordered by priority number)
        for rule in get_enabled_smart_rules(device.id):
            if self._rule_matches(rule, state, current_temp):
                return ImmersionDecision(
                    action=(rule.action == 'ON'),
                    source="smart_rule",
                    reason=rule.rule_name
                )
        
        # DEFAULT: Off
        return ImmersionDecision(action=False, source="default")
    
    def _rule_matches(
        self,
        rule: SmartRule,
        state: SystemState,
        device_temp: Optional[float]
    ) -> bool:
        """Evaluate all conditions using AND/OR logic"""
        conditions = []
        
        if rule.price_enabled:
            conditions.append(
                self._compare(state.current_price_pence, rule.price_operator, rule.price_threshold_pence)
            )
        if rule.soc_enabled:
            conditions.append(
                self._compare(state.battery_soc, rule.soc_operator, rule.soc_threshold_percent)
            )
        if rule.solar_enabled:
            conditions.append(
                self._compare(state.solar_power_kw, rule.solar_operator, rule.solar_threshold_kw)
            )
        if rule.temp_enabled and device_temp is not None:
            conditions.append(
                self._compare(device_temp, rule.temp_operator, rule.temp_threshold_c)
            )
        if rule.time_enabled:
            conditions.append(self._in_time_window(rule.time_start, rule.time_end))
        
        if not conditions:
            return False
        
        if rule.logic_operator == 'AND':
            return all(conditions)
        else:  # OR
            return any(conditions)
    
    def _temp_target_requires_heating(
        self,
        target: TemperatureTarget,
        current_temp: Optional[float]
    ) -> bool:
        """
        Returns True if we need to start heating now to meet the target.
        
        Logic:
        - If current_temp >= target_temp: already at target, no heating needed
        - Calculate hours needed: (target_temp - current_temp) / heating_rate
        - Calculate hours until target time
        - Turn on if: hours_until_target <= hours_needed + buffer
        """
        if current_temp is None:
            return False
        if current_temp >= target.target_temp_c:
            return False
        
        now = datetime.now()
        today_weekday = now.weekday()  # 0=Mon, 6=Sun
        
        # Check if today is in the target's days
        target_days = [int(d) for d in target.days_of_week.split(',')]
        if today_weekday not in target_days:
            return False
        
        # Calculate time until target
        target_dt = now.replace(
            hour=target.target_time.hour,
            minute=target.target_time.minute,
            second=0
        )
        if target_dt <= now:
            return False  # Target time already passed today
        
        hours_until_target = (target_dt - now).total_seconds() / 3600
        temp_deficit = target.target_temp_c - current_temp
        hours_needed = temp_deficit / target.heating_rate_c_per_hour
        buffer_hours = target.buffer_minutes / 60
        
        return hours_until_target <= (hours_needed + buffer_hours)
    
    def _compare(self, value: float, operator: str, threshold: float) -> bool:
        ops = {'<': lt, '<=': le, '>': gt, '>=': ge, '==': eq}
        return ops[operator](value, threshold)
    
    def _in_time_window(self, start: time, end: time) -> bool:
        now = datetime.now().time()
        if start <= end:
            return start <= now <= end
        else:  # Crosses midnight
            return now >= start or now <= end
```

---

## Action Executor

```python
# core/action_executor.py

class ActionExecutor:
    async def apply_battery(self, recommendation: OptimizationResult):
        """Apply battery optimizer recommendation to Home Assistant"""
        
        # Only call HA if mode actually changes
        current_mode = await ha_client.get_battery_mode()
        if current_mode != recommendation.mode:
            success = await ha_client.set_battery_mode(recommendation.mode)
            log_action("battery_mode", settings.ha_entity_battery_mode,
                      current_mode, recommendation.mode, "optimizer",
                      recommendation.reason, success)
        
        # Only call HA if discharge current changes
        current_current = await ha_client.get_discharge_current()
        if current_current != recommendation.discharge_current:
            success = await ha_client.set_discharge_current(recommendation.discharge_current)
            log_action("discharge_current", settings.ha_entity_discharge_current,
                      str(current_current), str(recommendation.discharge_current),
                      "optimizer", recommendation.reason, success)
    
    async def apply_immersion(self, device: ImmersionDevice, decision: ImmersionDecision):
        """Apply immersion decision to Home Assistant"""
        
        # Only call HA if state actually changes
        current_state = await ha_client.get_switch_state(device.switch_entity_id)
        if current_state != decision.action:
            success = await ha_client.set_switch(device.switch_entity_id, decision.action)
            log_action(
                "immersion",
                device.switch_entity_id,
                "on" if current_state else "off",
                "on" if decision.action else "off",
                decision.source,
                decision.reason,
                success
            )
            
            # Write to InfluxDB
            if influx_client.enabled:
                influx_client.write_immersion_action(device.name, decision)
```

---

## Optimizer Fixes

### Fix 1: Export Price (Fixed SEG Rate)

```python
# core/optimizer.py

def optimize(self, state, prices, load_forecast, settings):
    export_price = settings.export_price_pence  # e.g. 15.0p
    
    # Objective: Minimize cost
    prob += lpSum([
        (grid_import[t] * period_prices[t] * 0.5 -   # Import cost
         grid_export[t] * export_price * 0.5)          # Export revenue (fixed SEG rate)
        for t in range(num_periods)
    ])
```

### Fix 2: Configurable Constant Load Assumption

Household electricity consumption doesn't change based on battery/solar state, and varies second-to-second making real-time readings useless for a 5-minute optimizer cycle. A configurable constant is the correct approach.

```python
# core/optimizer.py

def optimize(self, state, prices, settings):
    assumed_load_kw = settings.assumed_load_kw  # e.g. 2.0 kW, configurable in UI
    
    # Use constant load for all forecast periods
    load_forecast = [assumed_load_kw] * num_periods
    
    # ... rest of LP optimization
```

---

## WebSocket Manager

```python
# websocket/manager.py

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send current state immediately on connect
        state = get_current_state()
        await websocket.send_json({"type": "state", "data": state})
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """Send message to all connected browsers"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.active_connections.remove(conn)
    
    async def broadcast_state(self, result: dict):
        await self.broadcast({"type": "optimization_result", "data": result})
    
    async def broadcast_prices(self, prices: list):
        await self.broadcast({"type": "prices_updated", "data": prices})

# FastAPI WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, receive any client messages
            data = await websocket.receive_text()
            # Handle client requests (e.g., "refresh_now")
            if data == "refresh":
                state = get_current_state()
                await websocket.send_json({"type": "state", "data": state})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

---

## API Endpoints Summary

### Optimization
```
GET  /api/v1/recommendation/now     - Current recommendation
POST /api/v1/prices/refresh         - Trigger price refresh
GET  /api/v1/prices/current         - Current + upcoming prices
GET  /api/v1/state/current          - Current system state
```

### Immersion Devices
```
GET    /api/v1/immersions/devices              - List all devices
POST   /api/v1/immersions/devices              - Add device
PUT    /api/v1/immersions/devices/{id}         - Update device
DELETE /api/v1/immersions/devices/{id}         - Remove device
GET    /api/v1/immersions/devices/{id}/status  - Live status + temp
```

### Smart Rules
```
GET    /api/v1/immersions/{id}/rules           - List rules
POST   /api/v1/immersions/{id}/rules           - Add rule
PUT    /api/v1/immersions/{id}/rules/{rid}     - Update rule
DELETE /api/v1/immersions/{id}/rules/{rid}     - Delete rule
POST   /api/v1/immersions/{id}/rules/reorder   - Reorder priorities
```

### Temperature Targets
```
GET    /api/v1/immersions/{id}/targets         - List targets
POST   /api/v1/immersions/{id}/targets         - Add target
PUT    /api/v1/immersions/{id}/targets/{tid}   - Update target
DELETE /api/v1/immersions/{id}/targets/{tid}   - Remove target
```

### Overrides
```
POST /api/v1/overrides/manual/set      - Set manual override
GET  /api/v1/overrides/manual/status   - Get override status
POST /api/v1/overrides/manual/clear    - Clear override
POST /api/v1/overrides/manual/clear-all - Clear all overrides
```

### History
```
GET /api/v1/history/recommendations    - Decision history
GET /api/v1/history/states             - System state history
GET /api/v1/history/actions            - HA action audit log
GET /api/v1/stats/daily                - Daily statistics
```

### Settings
```
GET  /api/v1/settings                  - All settings grouped by category
PUT  /api/v1/settings                  - Update multiple settings
GET  /api/v1/settings/{key}            - Single setting
PUT  /api/v1/settings/{key}            - Update single setting
POST /api/v1/settings/test/ha          - Test HA connection
POST /api/v1/settings/test/octopus     - Test Octopus API
POST /api/v1/settings/test/influx      - Test InfluxDB
GET  /api/v1/settings/export           - Export as JSON
POST /api/v1/settings/import           - Import from JSON
```

### System
```
GET  /health                           - Health check
POST /api/v1/system/optimize-now       - Force optimization run
POST /api/v1/system/pause              - Pause automation
POST /api/v1/system/resume             - Resume automation
```
