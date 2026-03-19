-- GridMind seed data
-- This is handled by Alembic migrations (002, 003, 006)
-- This file is kept as a reference / manual restore script

-- Immersion devices
INSERT INTO immersion_devices (name, display_name, switch_entity_id, temp_sensor_entity_id, sort_order)
VALUES
('main', 'Main Hot Water Tank', 'switch.immersion_switch', 'sensor.sonoff_1001e116e1_temperature', 1),
('lucy', 'Lucy''s Tank', 'switch.immersion_lucy_switch', 'sensor.t_h_sensor_with_external_probe_temperature_2', 2)
ON DUPLICATE KEY UPDATE display_name = VALUES(display_name);

-- Default smart rules (main tank)
INSERT INTO immersion_smart_rules
    (immersion_id, rule_name, priority, action, logic_operator, price_enabled, price_operator, price_threshold_pence)
SELECT 1, 'Negative Price', 1, 'ON', 'AND', TRUE, '<', 0.0
WHERE NOT EXISTS (SELECT 1 FROM immersion_smart_rules WHERE immersion_id = 1 AND rule_name = 'Negative Price');

INSERT INTO immersion_smart_rules
    (immersion_id, rule_name, priority, action, logic_operator,
     price_enabled, price_operator, price_threshold_pence,
     soc_enabled, soc_operator, soc_threshold_percent)
SELECT 1, 'Very Cheap + Full Battery', 2, 'ON', 'AND', TRUE, '<', 2.0, TRUE, '>=', 95.0
WHERE NOT EXISTS (SELECT 1 FROM immersion_smart_rules WHERE immersion_id = 1 AND rule_name = 'Very Cheap + Full Battery');

INSERT INTO immersion_smart_rules
    (immersion_id, rule_name, priority, action, logic_operator,
     solar_enabled, solar_operator, solar_threshold_kw,
     soc_enabled, soc_operator, soc_threshold_percent)
SELECT 1, 'Solar Surplus', 3, 'ON', 'AND', TRUE, '>=', 5.0, TRUE, '>=', 90.0
WHERE NOT EXISTS (SELECT 1 FROM immersion_smart_rules WHERE immersion_id = 1 AND rule_name = 'Solar Surplus');

INSERT INTO immersion_smart_rules
    (immersion_id, rule_name, priority, action, logic_operator, temp_enabled, temp_operator, temp_threshold_c)
SELECT 1, 'Overheat Protection', 99, 'OFF', 'AND', TRUE, '>=', 70.0
WHERE NOT EXISTS (SELECT 1 FROM immersion_smart_rules WHERE immersion_id = 1 AND rule_name = 'Overheat Protection');
