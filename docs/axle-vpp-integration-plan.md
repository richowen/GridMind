# Axle Energy VPP Native LP Integration - Implementation Plan

This document provides a highly detailed, instruction-level playbook for an AI coding agent to natively integrate Axle Energy's Virtual Power Plant (VPP) API into GridMind.

By embedding Axle's **£1.00+/kWh** export event periods directly into the math-based Linear Programming (LP) optimization matrix, GridMind can automatically prepare the home battery (e.g., pre-charging from cheap solar/grid slots) to execute maximum high-rate exports during grid stress windows.

API Bearer Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpbnRlcm5hbF9zaXRlX2lkIjoiNGI4MjNmMzYtZmQ0Mi00ZGI2LWI4OTItNzlmZWJkNjc1YWY0Iiwic2NvcGUiOlsidnBwOmhvbWVfYXNzaXN0YW50Il0sImV4cCI6MjY0NjMxNzQyMn0.7IW9rmTQ_ryrzdq0ssC4mjvCYURz2fqTLJC9AX2TRnQ

---

## 1. Context & API Intelligence

Axle Energy provides an "Events-Only" integration mode. While GridMind manages daily battery logistics locally, Axle commands exports *only* during active grid stress events.

### The Endpoint
* **Method**: `GET`
* **URL**: `https://api.axle.energy/vpp/home-assistant/event`
* **Headers**: `Authorization: Bearer <axle_vpp_token>`
* **Status Codes**: 
  * `200 OK`: Valid JSON representing the active/upcoming event, or a blank schema if idle.
* **Payload Shape**:
  ```json
  {
    "start_time": "2026-12-04T16:30:00Z",
    "end_time": "2026-12-04T17:30:00Z",
    "import_export": 1,
    "updated_at": "2026-12-04T12:05:00Z"
  }
  ```
  *(Note: Timestamps are RFC3339/ISO8601 UTC strings with `Z` suffix. If no event is scheduled, the API returns `null` or a payload missing `"start_time"`).*

---

## 2. Core Architectural Impact

```
                          ┌───────────────────────────┐
                          │   Axle VPP Cloud API      │
                          └─────────────┬─────────────┘
                                        │ (Fetch Event)
                                        ▼
┌─────────────────────────┐   ┌───────────────────────────┐
│ Octopus Agile API       ├──►│  scheduler.py             │
│ (Import Price Forecast) │   │  - Syncs Agile tariffs    │
└─────────────────────────┘   │  - Overlays Premium VPP   │
                              │    Export values (t-slots)│
                              └─────────┬─────────────────┘
                                        │
                                        ▼
                              ┌───────────────────────────┐
                              │  optimizer.py             │
                              │  - Runs PuLP LP Solver    │
                              │  - Triggers pre-charging  │
                              │  - Schedules max discharge│
                              └───────────────────────────┘
```

Currently, GridMind computes exports using a **single static setting** (`export_price_pence` defaults to 15p). To support VPP integration, we must refactor the LP solver to allow **dynamic per-period export rates**:
1. Standard periods get the basic SEG export rate (e.g., 15p).
2. Axle VPP event slots get overridden with the premium rate (e.g., 100p or 200p).
3. The LP objective function seamlessly solves for peak-revenue: pre-charging the battery beforehand and discharging at maximum capacity during the event.

---

## 3. Phased Implementation Plan

### Phase 1: Database Migration & Config Setup
Add configurations to support the Axle API integration.

1. **Create Alembic Migration**:
   Create a migration script (e.g., `backend/alembic/versions/012_axle_vpp_settings.py`):
   ```python
   # 012_axle_vpp_settings.py
   from alembic import op

   def upgrade() -> None:
       op.execute("""
           INSERT IGNORE INTO system_settings (`key`, `value`, value_type, category, description) VALUES
           ('axle_vpp_enabled', 'false', 'bool', 'optimization', 'Enable native Axle VPP grid export tracking'),
           ('axle_vpp_token', '', 'string', 'optimization', 'Axle API Authorization Bearer Token'),
           ('axle_vpp_export_price_pence', '100.0', 'float', 'optimization', 'Premium export rate paid per kWh during active VPP events')
       """)

   def downgrade() -> None:
       op.execute("""
           DELETE FROM system_settings WHERE `key` IN ('axle_vpp_enabled', 'axle_vpp_token', 'axle_vpp_export_price_pence')
       """)
   ```

---

### Phase 2: Create the Axle API Client
Implement `backend/app/services/axle.py` utilizing a shared `httpx.AsyncClient` mapping connection configurations cleanly.

```python
# backend/app/services/axle.py
import logging
from datetime import datetime, timezone
from typing import Optional, tuple
import httpx
from app.core.settings_cache import get_settings, get_setting_bool

logger = logging.getLogger(__name__)

class AxleVPPClient:
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self._settings_key: Optional[str] = None

    def _get_client(self) -> httpx.AsyncClient:
        settings = get_settings()
        key = f"{settings.get('axle_vpp_token')}"
        if self._client is None or self._client.is_closed or self._settings_key != key:
            self._client = httpx.AsyncClient(timeout=10)
            self._settings_key = key
        return self._client

    async def get_active_event(self) -> Optional[tuple[datetime, datetime]]:
        """
        Poll Axle API. Returns (start_utc, end_utc) naive datetimes
        matching GridMind's DB timezone structure, or None.
        """
        if not get_setting_bool("axle_vpp_enabled", False):
            return None

        settings = get_settings()
        token = settings.get("axle_vpp_token")
        if not token:
            logger.warning("Axle VPP is enabled but axle_vpp_token is empty")
            return None

        url = "https://api.axle.energy/vpp/home-assistant/event"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        try:
            client = self._get_client()
            resp = await client.get(url, headers=headers)
            if resp.status_code == 401:
                logger.error("Axle API returned 401 Unauthorized. Verify your token.")
                return None
            resp.raise_for_status()
            data = resp.json()

            if not data or "start_time" not in data:
                return None

            # Parse and convert to naive UTC (GridMind standard DB timezone)
            start_utc = datetime.fromisoformat(data["start_time"].replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
            end_utc = datetime.fromisoformat(data["end_time"].replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
            
            return start_utc, end_utc
        except Exception as e:
            logger.error(f"Axle API fetch failed: {e}")
            return None

axle_client = AxleVPPClient()
```

---

### Phase 3: Update the LP Optimization Pipeline

To allow dynamic per-period export rates, refactor:
1. `backend/app/core/optimizer.py` to accept per-period export limits and prices.
2. `backend/app/core/scheduler.py` to fetch active events and calculate prices.

#### 1. Modify `PricePeriod` Schema in `optimizer.py`
Change:
```python
@dataclass
class PricePeriod:
    valid_from: datetime
    valid_to: datetime
    price_pence: float          # Import rate
    export_price_pence: float   # Add this - custom export rate
```

#### 2. Update LP Equations in `optimizer.py`
Inside `_run_lp()` inside `backend/app/core/optimizer.py`:
Locate the objective function line:
```python
# OLD:
# prob += pulp.lpSum([
#     grid_import[t] * period_prices[t] * 0.5
#     - grid_export[t] * export_price_pence * 0.5
#     for t in range(num_periods)
# ])

# NEW:
prob += pulp.lpSum([
    grid_import[t] * period_prices[t] * 0.5
    - grid_export[t] * periods[t].export_price_pence * 0.5
    for t in range(num_periods)
])
```

#### 3. Update Scheduled loop overlay in `scheduler.py`
Inside `optimization_loop()` in `backend/app/core/scheduler.py`, fetch standard SEG export price alongside VPP event:
```python
            from app.services.axle import axle_client
            vpp_event = await axle_client.get_active_event()  # returns (start, end) or None
            
            default_export_price = get_setting_float("export_price_pence", 15.0)
            vpp_export_price = get_setting_float("axle_vpp_export_price_pence", 100.0)

            price_periods = []
            for p in prices_rows:
                # Detect if this planning slot falls inside active Axle event window
                is_vpp_slot = False
                if vpp_event:
                    start, end = vpp_event
                    # Standard check: does slot overlap with event boundary?
                    is_vpp_slot = (p.valid_from >= start and p.valid_to <= end)

                export_rate = vpp_export_price if is_vpp_slot else default_export_price
                
                price_periods.append(PricePeriod(
                    valid_from=p.valid_from,
                    valid_to=p.valid_to,
                    price_pence=p.price_pence,
                    export_price_pence=export_rate
                ))
```

*This guarantees the optimization matrix will see positive feedback from exporting at 100p during the event, naturally finding the local minimum by storing grid power beforehand.*

---

### Phase 4: Rules Engine Safe-Guarding
During grid events, home appliances and immersion heaters should be throttled or disabled to maximize export capacity.

Inside `backend/app/core/rules_engine.py`:
Add a guard condition that evaluates active VPP status and disables immersion loads if configured.
```python
        # Check if immersion load shedding is desired during VPP stress hours
        # Add 'disable_during_vpp' check on smart rules or defaults
```

---

### Phase 5: Broadcasters & Real-Time Client Signals
Expose when an event is active or pending to the UI.

1. In `app/websocket/manager.py` and `scheduler.py`'s payload, add:
   ```json
   "vpp_event": {
       "is_active": true,
       "start": "2026-12-04T16:30:00Z",
       "end": "2026-12-04T17:30:00Z"
   }
   ```
2. Update React Frontend:
   * Render a clean banner on `Dashboard.tsx` when `vpp_event.is_active` is true.
   * Highlight premium price-nodes dynamically on `Prices.tsx` and `Why.tsx`.

---

## 4. Verification & Testing

Always verify correctness before proposing changes by creating and running automated test fixtures. 

Inside `backend/tests/test_axle_vpp.py`:
```python
import pytest
from datetime import datetime, timedelta
from app.core.optimizer import BatteryOptimizer, OptimizationInput, PricePeriod

def test_vpp_precharge():
    """Verify that high-export rates trigger pre-charging logic."""
    opt = BatteryOptimizer()
    base_time = datetime.utcnow()

    # Define simple 4-period setup
    # 0: Agile import 10p, Export 15p (Standard)
    # 1: Agile import 10p, Export 15p (Standard)
    # 2: Agile import 25p, Export 100p (VPP Stress slot!)
    # 3: Agile import 15p, Export 15p (Standard)
    prices = [
        PricePeriod(base_time, base_time+timedelta(minutes=30), 10.0, 15.0),
        PricePeriod(base_time+timedelta(minutes=30), base_time+timedelta(hours=1), 10.0, 15.0),
        PricePeriod(base_time+timedelta(hours=1), base_time+timedelta(minutes=90), 25.0, 100.0), # VPP Event
        PricePeriod(base_time+timedelta(minutes=90), base_time+timedelta(hours=2), 15.0, 15.0),
    ]

    inp = OptimizationInput(
        battery_soc=20.0, # low battery
        solar_power_kw=0.0,
        prices=prices
    )

    res = opt.optimize(inp)
    
    # Assert optimizer results cleanly trigger pre-charge action prior to vpp slot
    assert res.optimization_status == "optimal"
```

To run verification, execute:
```bash
PYTHONPATH=. backend/venv/Scripts/python -m pytest backend/tests/test_axle_vpp.py
```
