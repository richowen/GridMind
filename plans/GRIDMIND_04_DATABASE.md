# GridMind — Database Schema

## Overview

GridMind uses MariaDB with Alembic for versioned migrations. All schema changes are tracked and repeatable.

Database name: `gridmind`

---

## Existing Tables (migrated from battery_optimizer)

These tables are carried over from V2 with minor additions:

### electricity_prices
```sql
CREATE TABLE electricity_prices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    valid_from DATETIME NOT NULL,
    valid_to DATETIME NOT NULL,
    price_pence FLOAT NOT NULL,
    classification VARCHAR(20),  -- 'negative', 'cheap', 'normal', 'expensive'
    INDEX idx_valid_from (valid_from),
    INDEX idx_valid_to (valid_to)
);
```

### optimization_results
```sql
CREATE TABLE optimization_results (
    id INT PRIMARY KEY AUTO_INCREMENT,
    timestamp DATETIME NOT NULL,
    current_soc FLOAT,
    current_solar_kw FLOAT,
    current_price_pence FLOAT,
    recommended_mode VARCHAR(50),
    recommended_discharge_current INT,
    optimization_status VARCHAR(20),
    optimization_time_ms FLOAT,
    objective_value FLOAT,
    decision_reason TEXT,
    next_action_time DATETIME,
    INDEX idx_timestamp (timestamp)
);
```

### system_states
```sql
CREATE TABLE system_states (
    id INT PRIMARY KEY AUTO_INCREMENT,
    timestamp DATETIME NOT NULL,
    battery_soc FLOAT,
    battery_mode VARCHAR(50),
    battery_discharge_current INT,
    solar_power_kw FLOAT,
    solar_forecast_today_kwh FLOAT,
    solar_forecast_next_hour_kw FLOAT,
    current_price_pence FLOAT,
    immersion_main_on BOOLEAN,
    immersion_lucy_on BOOLEAN,
    INDEX idx_timestamp (timestamp)
);
```

---

## New Tables

### immersion_devices
Device registry — supports N immersion heaters.

```sql
CREATE TABLE immersion_devices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,           -- 'main', 'lucy', etc.
    display_name VARCHAR(100) NOT NULL,          -- 'Main Hot Water Tank'
    switch_entity_id VARCHAR(150) NOT NULL,      -- 'switch.immersion_switch'
    temp_sensor_entity_id VARCHAR(150),          -- NULL if no temp sensor
    is_enabled BOOLEAN DEFAULT TRUE,
    sort_order INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Seed data
INSERT INTO immersion_devices (name, display_name, switch_entity_id, temp_sensor_entity_id, sort_order) VALUES
('main', 'Main Hot Water Tank', 'switch.immersion_switch', 'sensor.sonoff_1001e116e1_temperature', 1),
('lucy', "Lucy's Tank", 'switch.immersion_lucy_switch', 'sensor.t_h_sensor_with_external_probe_temperature_2', 2);
```

### immersion_smart_rules
Configurable rules engine — all thresholds stored here, none hardcoded.

```sql
CREATE TABLE immersion_smart_rules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    immersion_id INT NOT NULL,
    rule_name VARCHAR(100) NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    priority INT DEFAULT 10,                     -- Lower = higher priority
    action VARCHAR(10) NOT NULL,                 -- 'ON' or 'OFF'
    logic_operator VARCHAR(3) DEFAULT 'AND',     -- 'AND' or 'OR' between conditions
    
    -- Price condition
    price_enabled BOOLEAN DEFAULT FALSE,
    price_operator VARCHAR(5),                   -- '<', '<=', '>', '>='
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
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (immersion_id) REFERENCES immersion_devices(id) ON DELETE CASCADE,
    INDEX idx_device_priority (immersion_id, is_enabled, priority)
);

-- Example seed rules (user can modify/delete via UI)
INSERT INTO immersion_smart_rules 
    (immersion_id, rule_name, priority, action, logic_operator, price_enabled, price_operator, price_threshold_pence)
VALUES
    (1, 'Negative Price', 1, 'ON', 'AND', TRUE, '<', 0.0),
    (2, 'Negative Price', 1, 'ON', 'AND', TRUE, '<', 0.0);

INSERT INTO immersion_smart_rules 
    (immersion_id, rule_name, priority, action, logic_operator, 
     price_enabled, price_operator, price_threshold_pence,
     soc_enabled, soc_operator, soc_threshold_percent)
VALUES
    (1, 'Very Cheap + Full Battery', 2, 'ON', 'AND', TRUE, '<', 2.0, TRUE, '>=', 95.0),
    (2, 'Very Cheap + Full Battery', 2, 'ON', 'AND', TRUE, '<', 2.0, TRUE, '>=', 95.0);

INSERT INTO immersion_smart_rules 
    (immersion_id, rule_name, priority, action, logic_operator,
     solar_enabled, solar_operator, solar_threshold_kw,
     soc_enabled, soc_operator, soc_threshold_percent)
VALUES
    (1, 'Solar Surplus', 3, 'ON', 'AND', TRUE, '>=', 5.0, TRUE, '>=', 90.0),
    (2, 'Solar Surplus', 3, 'ON', 'AND', TRUE, '>=', 5.0, TRUE, '>=', 90.0);

INSERT INTO immersion_smart_rules 
    (immersion_id, rule_name, priority, action, logic_operator, temp_enabled, temp_operator, temp_threshold_c)
VALUES
    (1, 'Overheat Protection', 99, 'OFF', 'AND', TRUE, '>=', 70.0),
    (2, 'Overheat Protection', 99, 'OFF', 'AND', TRUE, '>=', 70.0);
```

### temperature_targets
"Ensure X°C by Y time" goals.

```sql
CREATE TABLE temperature_targets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    immersion_id INT NOT NULL,
    target_name VARCHAR(100) NOT NULL,           -- 'Morning Hot Water'
    target_temp_c FLOAT NOT NULL,                -- e.g. 30.0
    target_time TIME NOT NULL,                   -- e.g. 09:00
    days_of_week VARCHAR(20) NOT NULL,           -- e.g. '0,1,2,3,4' (Mon-Fri)
    heating_rate_c_per_hour FLOAT DEFAULT 5.0,   -- Configurable per tank
    buffer_minutes INT DEFAULT 30,               -- Safety buffer
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (immersion_id) REFERENCES immersion_devices(id) ON DELETE CASCADE
);
```

### manual_overrides
(Existing table, kept as-is but now references immersion_id instead of name)

```sql
CREATE TABLE manual_overrides (
    id INT PRIMARY KEY AUTO_INCREMENT,
    immersion_id INT NOT NULL,                   -- FK to immersion_devices
    immersion_name VARCHAR(50) NOT NULL,         -- Kept for compatibility
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    desired_state BOOLEAN NOT NULL,
    source VARCHAR(50) DEFAULT 'user',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    cleared_at DATETIME NULL,
    cleared_by VARCHAR(50) NULL,
    
    FOREIGN KEY (immersion_id) REFERENCES immersion_devices(id),
    INDEX idx_active_immersion (immersion_id, is_active, expires_at)
);
```

### system_actions
Audit log of every HA call made.

```sql
CREATE TABLE system_actions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action_type VARCHAR(50) NOT NULL,            -- 'battery_mode', 'discharge_current', 'immersion'
    entity_id VARCHAR(150) NOT NULL,
    old_value VARCHAR(100),
    new_value VARCHAR(100) NOT NULL,
    source VARCHAR(50) NOT NULL,                 -- 'optimizer', 'schedule', 'manual_override', 'temperature_target', 'smart_rule', 'default'
    reason TEXT,
    success BOOLEAN DEFAULT TRUE,
    
    INDEX idx_timestamp (timestamp),
    INDEX idx_action_type (action_type),
    INDEX idx_entity (entity_id)
);
```

### system_settings
All configuration — replaces `.env` for runtime settings.

```sql
CREATE TABLE system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    value_type VARCHAR(20) DEFAULT 'string',     -- 'string', 'float', 'int', 'bool'
    category VARCHAR(50) NOT NULL,               -- 'battery', 'ha', 'ha_entities', 'octopus', 'prices', 'optimization', 'influxdb', 'system'
    description TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Seed data (initial values from .env)
INSERT INTO system_settings (key, value, value_type, category, description) VALUES
-- Battery
('battery_capacity_kwh', '10.6', 'float', 'battery', 'Battery capacity in kWh'),
('battery_max_charge_kw', '10.5', 'float', 'battery', 'Max charge rate in kW'),
('battery_max_discharge_kw', '5.0', 'float', 'battery', 'Max discharge rate in kW'),
('battery_efficiency', '0.95', 'float', 'battery', 'Round-trip efficiency (0-1)'),
('battery_min_soc', '10', 'int', 'battery', 'Minimum state of charge %'),
('battery_max_soc', '100', 'int', 'battery', 'Maximum state of charge %'),
-- HA Connection
('ha_url', 'http://192.168.1.3:8123', 'string', 'ha', 'Home Assistant URL'),
('ha_token', '', 'string', 'ha', 'HA long-lived access token'),
-- HA Entity IDs
('ha_entity_battery_soc', 'sensor.foxinverter_battery_soc', 'string', 'ha_entities', 'Battery SoC entity'),
('ha_entity_battery_mode', 'select.foxinverter_work_mode', 'string', 'ha_entities', 'Work mode entity'),
('ha_entity_discharge_current', 'number.foxinverter_max_discharge_current', 'string', 'ha_entities', 'Discharge current entity'),
('ha_entity_solar_power', 'sensor.pv_power_foxinverter', 'string', 'ha_entities', 'Solar power entity'),
('ha_entity_solar_forecast_today', 'sensor.solcast_pv_forecast_forecast_remaining_today', 'string', 'ha_entities', 'Solar forecast today'),
('ha_entity_solar_forecast_1hr', 'sensor.solcast_pv_forecast_power_in_1_hour', 'string', 'ha_entities', 'Solar forecast 1hr'),
-- Octopus
('octopus_product', 'AGILE-24-10-01', 'string', 'octopus', 'Octopus product code'),
('octopus_tariff', 'E-1R-AGILE-24-10-01-E', 'string', 'octopus', 'Octopus tariff code'),
('octopus_region', 'E', 'string', 'octopus', 'Octopus region code'),
-- Price Classification
('price_negative_threshold', '0', 'float', 'prices', 'Below this = negative price (p/kWh)'),
('price_cheap_threshold', '10', 'float', 'prices', 'Below this = cheap price (p/kWh)'),
('price_expensive_threshold', '25', 'float', 'prices', 'Above this = expensive price (p/kWh)'),
-- Optimization
('optimization_horizon_hours', '24', 'int', 'optimization', 'LP lookahead horizon in hours'),
('optimization_interval_minutes', '5', 'int', 'optimization', 'How often to run optimization'),
('price_refresh_interval_minutes', '30', 'int', 'optimization', 'How often to fetch prices'),
('grid_import_limit_kw', '15.0', 'float', 'optimization', 'Max grid import in kW'),
('grid_export_limit_kw', '5.0', 'float', 'optimization', 'Max grid export in kW'),
('export_price_pence', '15.0', 'float', 'optimization', 'Fixed SEG export rate in p/kWh'),
('assumed_load_kw', '2.0', 'float', 'optimization', 'Assumed constant household load for optimizer (kW)'),
-- InfluxDB
('influx_enabled', 'true', 'bool', 'influxdb', 'Enable InfluxDB logging'),
('influx_url', 'http://192.168.1.64:8086', 'string', 'influxdb', 'InfluxDB URL'),
('influx_token', '', 'string', 'influxdb', 'InfluxDB API token'),
('influx_org', 'unraid', 'string', 'influxdb', 'InfluxDB organisation'),
('influx_bucket', 'battery-optimizer', 'string', 'influxdb', 'InfluxDB bucket name'),
-- System
('timezone', 'Europe/London', 'string', 'system', 'System timezone');
```

---

## InfluxDB Compatibility

### Existing Measurements — Preserved Exactly

| Measurement | Tags | Fields | Status |
|-------------|------|--------|--------|
| `electricity_price` | `classification`, `is_negative` | `price_pence`, `price_pounds` | ✅ Unchanged |
| `price_analysis` | `data_type` | `min_price`, `max_price`, `mean_price`, `median_price`, `cheap_threshold`, `expensive_threshold`, `negative_count`, `cheap_count`, `expensive_count`, `total_periods` | ✅ Unchanged |
| `battery_decision` | `mode`, `optimization_status` | `discharge_current`, `expected_soc`, `immersion_main`, `immersion_lucy`, `optimization_time_ms` | ✅ Unchanged |
| `system_state` | `battery_mode` | `battery_soc`, `solar_power_kw`, `solar_forecast_today_kwh`, `discharge_current`, `immersion_main_on`, `immersion_lucy_on`, `current_price_pence` | ✅ Unchanged |

### New Fields (Additive Only)

**`system_state` gets new optional fields:**
```
temp_main_c            - Main immersion temperature
temp_lucy_c            - Lucy's tank temperature
```

**New measurement: `immersion_action`**
```
Tags:   device_name, action, source
Fields: success (bool), reason (string)
```

---

## Alembic Migration Files

```
alembic/versions/
├── 001_initial_schema.py          ← electricity_prices, optimization_results, system_states, price_analysis
├── 002_immersion_devices.py       ← immersion_devices (with seed data)
├── 003_rules_engine.py            ← immersion_smart_rules + temperature_targets (with seed rules)
├── 004_overrides.py               ← manual_overrides
├── 005_system_actions.py          ← system_actions audit log
└── 006_system_settings.py         ← system_settings (with all seed data)
```

Each migration is reversible (has `upgrade()` and `downgrade()` functions).
