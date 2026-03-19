"""006 — System settings table with full seed data (all config in DB).

Revision ID: 006
Revises: 005
Create Date: 2025-01-01
"""

from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("value_type", sa.String(20), default="string"),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.execute("""
        INSERT INTO system_settings (key, value, value_type, category, description) VALUES
        ('battery_capacity_kwh', '10.6', 'float', 'battery', 'Battery capacity in kWh'),
        ('battery_max_charge_kw', '10.5', 'float', 'battery', 'Max charge rate in kW'),
        ('battery_max_discharge_kw', '5.0', 'float', 'battery', 'Max discharge rate in kW'),
        ('battery_efficiency', '0.95', 'float', 'battery', 'Round-trip efficiency (0-1)'),
        ('battery_min_soc', '10', 'int', 'battery', 'Minimum state of charge %'),
        ('battery_max_soc', '100', 'int', 'battery', 'Maximum state of charge %'),
        ('ha_url', 'http://192.168.1.3:8123', 'string', 'ha', 'Home Assistant URL'),
        ('ha_token', '', 'string', 'ha', 'HA long-lived access token'),
        ('ha_entity_battery_soc', 'sensor.foxinverter_battery_soc', 'string', 'ha_entities', 'Battery SoC entity'),
        ('ha_entity_battery_mode', 'select.foxinverter_work_mode', 'string', 'ha_entities', 'Work mode entity'),
        ('ha_entity_discharge_current', 'number.foxinverter_max_discharge_current', 'string', 'ha_entities', 'Discharge current entity'),
        ('ha_entity_solar_power', 'sensor.pv_power_foxinverter', 'string', 'ha_entities', 'Solar power entity'),
        ('ha_entity_solar_forecast_today', 'sensor.solcast_pv_forecast_forecast_remaining_today', 'string', 'ha_entities', 'Solar forecast today'),
        ('ha_entity_solar_forecast_1hr', 'sensor.solcast_pv_forecast_power_in_1_hour', 'string', 'ha_entities', 'Solar forecast 1hr'),
        ('octopus_product', 'AGILE-24-10-01', 'string', 'octopus', 'Octopus product code'),
        ('octopus_tariff', 'E-1R-AGILE-24-10-01-E', 'string', 'octopus', 'Octopus tariff code'),
        ('octopus_region', 'E', 'string', 'octopus', 'Octopus region code'),
        ('price_negative_threshold', '0', 'float', 'prices', 'Below this = negative price (p/kWh)'),
        ('price_cheap_threshold', '10', 'float', 'prices', 'Below this = cheap price (p/kWh)'),
        ('price_expensive_threshold', '25', 'float', 'prices', 'Above this = expensive price (p/kWh)'),
        ('optimization_horizon_hours', '24', 'int', 'optimization', 'LP lookahead horizon in hours'),
        ('optimization_interval_minutes', '5', 'int', 'optimization', 'How often to run optimization'),
        ('price_refresh_interval_minutes', '30', 'int', 'optimization', 'How often to fetch prices'),
        ('grid_import_limit_kw', '15.0', 'float', 'optimization', 'Max grid import in kW'),
        ('grid_export_limit_kw', '5.0', 'float', 'optimization', 'Max grid export in kW'),
        ('export_price_pence', '15.0', 'float', 'optimization', 'Fixed SEG export rate in p/kWh'),
        ('assumed_load_kw', '2.0', 'float', 'optimization', 'Assumed constant household load for optimizer (kW)'),
        ('influx_enabled', 'true', 'bool', 'influxdb', 'Enable InfluxDB logging'),
        ('influx_url', 'http://192.168.1.64:8086', 'string', 'influxdb', 'InfluxDB URL'),
        ('influx_token', '', 'string', 'influxdb', 'InfluxDB API token'),
        ('influx_org', 'unraid', 'string', 'influxdb', 'InfluxDB organisation'),
        ('influx_bucket', 'battery-optimizer', 'string', 'influxdb', 'InfluxDB bucket name'),
        ('timezone', 'Europe/London', 'string', 'system', 'System timezone')
    """)


def downgrade() -> None:
    op.drop_table("system_settings")
