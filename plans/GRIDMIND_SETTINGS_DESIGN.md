# GridMind — Settings Page Design

## Settings Storage Strategy

All settings are stored in a `system_settings` key-value table in MariaDB. No restart required when settings change — the system reads them dynamically each cycle.

```sql
CREATE TABLE system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    value_type VARCHAR(20) DEFAULT 'string',  -- 'string', 'float', 'int', 'bool'
    category VARCHAR(50) NOT NULL,
    description TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

Only `LOG_LEVEL` stays in `.env` (requires restart). Everything else is in the DB.

---

## Settings Page UI

```
┌─────────────────────────────────────────────────────────────┐
│  Settings                                    [Save Changes] │
│                                                             │
│  ── BATTERY CONFIGURATION ─────────────────────────────── │
│  Capacity:               [10.6] kWh                        │
│  Max Charge Rate:        [10.5] kW                         │
│  Max Discharge Rate:     [5.0]  kW                         │
│  Round-trip Efficiency:  [95]   %                          │
│  Minimum SoC:            [10]   %                          │
│  Maximum SoC:            [100]  %                          │
│                                                             │
│  ── HOME ASSISTANT CONNECTION ─────────────────────────── │
│  HA URL:    [http://192.168.1.3:8123]                      │
│  HA Token:  [••••••••••••••••]        [Test Connection ✓]  │
│                                                             │
│  ── BATTERY ENTITY IDs ────────────────────────────────── │
│  Battery SoC:            [sensor.foxinverter_battery_soc]  │
│  Work Mode:              [select.foxinverter_work_mode]    │
│  Discharge Current:      [number.foxinverter_max_discharge_current] │
│  Solar Power:            [sensor.pv_power_foxinverter]     │
│  Solar Forecast Today:   [sensor.solcast_pv_forecast_forecast_remaining_today] │
│  Solar Forecast 1hr:     [sensor.solcast_pv_forecast_power_in_1_hour] │
│                                                             │
│  ── OCTOPUS ENERGY ────────────────────────────────────── │
│  Product Code:  [AGILE-24-10-01]                           │
│  Tariff Code:   [E-1R-AGILE-24-10-01-E]                   │
│  Region:        [E ▼]  (dropdown: A through P)             │
│  [Test API Connection ✓]                                   │
│                                                             │
│  ── PRICE CLASSIFICATION ──────────────────────────────── │
│  Negative threshold:   [0]   p/kWh  (below = negative)    │
│  Cheap threshold:      [10]  p/kWh  (below = cheap)       │
│  Expensive threshold:  [25]  p/kWh  (above = expensive)   │
│  ℹ These thresholds affect chart colours and optimizer     │
│                                                             │
│  ── OPTIMIZATION ──────────────────────────────────────── │
│  Optimization horizon:   [24]  hours                       │
│  Optimization interval:  [5]   minutes                     │
│  Price refresh interval: [30]  minutes                     │
│  Grid import limit:      [15.0] kW                         │
│  Grid export limit:      [5.0]  kW                         │
│  Export price (SEG):     [15.0] p/kWh  (fixed rate paid for export) │
│                                                             │
│  ── LOAD ASSUMPTION ───────────────────────────────────── │
│  Assumed household load: [2.0] kW                          │
│  ℹ Used by the LP optimizer for all forecast periods       │
│  ℹ Household consumption doesn't change based on battery   │
│                                                             │
│  ── INFLUXDB (optional) ───────────────────────────────── │
│  Enabled:  [✅ toggle]                                     │
│  URL:      [http://192.168.1.64:8086]                      │
│  Token:    [••••••••••••••••]                              │
│  Org:      [unraid]                                        │
│  Bucket:   [battery-optimizer]                             │
│  [Test Connection ✓]                                       │
│                                                             │
│  ── SYSTEM ────────────────────────────────────────────── │
│  Timezone:  [Europe/London ▼]                              │
│  [Export Settings as JSON]  [Import Settings from JSON]    │
│  [Reset to Defaults]                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Settings Keys (DB seed data)

| Key | Default Value | Category | Description |
|-----|--------------|----------|-------------|
| `battery_capacity_kwh` | `10.6` | battery | Battery capacity in kWh |
| `battery_max_charge_kw` | `10.5` | battery | Max charge rate in kW |
| `battery_max_discharge_kw` | `5.0` | battery | Max discharge rate in kW |
| `battery_efficiency` | `0.95` | battery | Round-trip efficiency (0-1) |
| `battery_min_soc` | `10` | battery | Minimum state of charge % |
| `battery_max_soc` | `100` | battery | Maximum state of charge % |
| `ha_url` | `http://192.168.1.3:8123` | ha | Home Assistant URL |
| `ha_token` | *(from .env initially)* | ha | HA long-lived access token |
| `ha_entity_battery_soc` | `sensor.foxinverter_battery_soc` | ha_entities | Battery SoC entity |
| `ha_entity_battery_mode` | `select.foxinverter_work_mode` | ha_entities | Work mode entity |
| `ha_entity_discharge_current` | `number.foxinverter_max_discharge_current` | ha_entities | Discharge current entity |
| `ha_entity_solar_power` | `sensor.pv_power_foxinverter` | ha_entities | Solar power entity |
| `ha_entity_solar_forecast_today` | `sensor.solcast_pv_forecast_forecast_remaining_today` | ha_entities | Solar forecast today entity |
| `ha_entity_solar_forecast_1hr` | `sensor.solcast_pv_forecast_power_in_1_hour` | ha_entities | Solar forecast 1hr entity |
| `octopus_product` | `AGILE-24-10-01` | octopus | Octopus product code |
| `octopus_tariff` | `E-1R-AGILE-24-10-01-E` | octopus | Octopus tariff code |
| `octopus_region` | `E` | octopus | Octopus region code |
| `price_negative_threshold` | `0` | prices | Below this = negative price |
| `price_cheap_threshold` | `10` | prices | Below this = cheap price |
| `price_expensive_threshold` | `25` | prices | Above this = expensive price |
| `optimization_horizon_hours` | `24` | optimization | LP lookahead horizon |
| `optimization_interval_minutes` | `5` | optimization | How often to optimize |
| `price_refresh_interval_minutes` | `30` | optimization | How often to fetch prices |
| `grid_import_limit_kw` | `15.0` | optimization | Max grid import |
| `grid_export_limit_kw` | `5.0` | optimization | Max grid export |
| `export_price_pence` | `15.0` | optimization | Fixed SEG export rate in p/kWh |
| `assumed_load_kw` | `2.0` | optimization | Assumed constant household load for optimizer (kW) |
| `influx_enabled` | `true` | influxdb | Enable InfluxDB logging |
| `influx_url` | `http://192.168.1.64:8086` | influxdb | InfluxDB URL |
| `influx_token` | *(from .env initially)* | influxdb | InfluxDB API token |
| `influx_org` | `unraid` | influxdb | InfluxDB organisation |
| `influx_bucket` | `battery-optimizer` | influxdb | InfluxDB bucket name |
| `timezone` | `Europe/London` | system | System timezone |

---

## Settings API Endpoints

```
GET  /api/v1/settings              - Get all settings (grouped by category)
PUT  /api/v1/settings              - Update multiple settings at once
GET  /api/v1/settings/{key}        - Get single setting
PUT  /api/v1/settings/{key}        - Update single setting

POST /api/v1/settings/test/ha      - Test HA connection with current settings
POST /api/v1/settings/test/octopus - Test Octopus API connection
POST /api/v1/settings/test/influx  - Test InfluxDB connection

GET  /api/v1/settings/export       - Export all settings as JSON
POST /api/v1/settings/import       - Import settings from JSON
POST /api/v1/settings/reset        - Reset to default values
```

---

## Optimizer Corrections Required

The V2 optimizer has two bugs that GridMind will fix:

### Bug 1: Export Price (Wrong Formula)
**V2 (wrong):** `export_revenue = grid_export × import_price × 0.15`
This makes export revenue depend on the import price, which is incorrect.

**GridMind (correct):** `export_revenue = grid_export × export_price_pence`
Where `export_price_pence` is the fixed SEG rate (currently 15p/kWh), stored in settings.

```python
# V2 objective (wrong):
prob += lpSum([
    grid_import[t] * period_prices[t] * 0.5 -
    grid_export[t] * period_prices[t] * 0.5 * 0.15  # ← WRONG: ties export to import price
    for t in range(num_periods)
])

# GridMind objective (correct):
prob += lpSum([
    grid_import[t] * period_prices[t] * 0.5 -
    grid_export[t] * export_price_pence * 0.5  # ← CORRECT: fixed SEG rate
    for t in range(num_periods)
])
```

### Fix 2: Configurable Constant Load Assumption
**V2:** Uses hardcoded 2kW constant — not configurable.

**GridMind:** Uses a configurable `assumed_load_kw` setting (default 2.0 kW), editable in the Settings UI. Household electricity consumption doesn't change based on battery/solar state, and real-time CT clamp readings are too noisy for a 5-minute optimizer cycle. A configurable constant is the correct approach.

---

## Migration from .env to DB Settings

On first startup, GridMind reads `.env` values and seeds the `system_settings` table. After that, the DB is the source of truth. The `.env` file only needs:

```env
# Minimal .env for GridMind (everything else in DB)
DB_HOST=mariadb
DB_PORT=3306
DB_USER=gridmind
DB_PASSWORD=your_password
DB_NAME=gridmind
LOG_LEVEL=INFO
```

Sensitive values (HA token, InfluxDB token) are stored in the DB but displayed masked in the UI. They can be updated via the Settings page.
