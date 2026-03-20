"""007 — Add optimizer tuning settings: force_charge_threshold_kw, battery_voltage_v.

Revision ID: 007
Revises: 006
Create Date: 2025-01-01
"""

from alembic import op

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # NOTE: INSERT IGNORE is MySQL/MariaDB-specific syntax.
    # This migration assumes a MySQL-compatible database (as used in production).
    # For PostgreSQL use INSERT ... ON CONFLICT DO NOTHING; for SQLite use INSERT OR IGNORE.
    op.execute("""
        INSERT IGNORE INTO system_settings (`key`, `value`, value_type, category, description) VALUES
        ('force_charge_threshold_kw', '0.5', 'float', 'optimization',
         'Minimum LP charge power (kW) in period 0 to trigger Force Charge or Force Discharge mode'),
        ('battery_voltage_v', '48.0', 'float', 'battery',
         'Fallback battery voltage (V) for kW→amps conversion when live sensor is unavailable'),
        ('ha_entity_charge_rate', 'sensor.foxinverter_bms_charge_rate', 'string', 'ha_entities',
         'BMS live charge rate entity (kW) — used to cap LP charge upper bound'),
        ('ha_entity_battery_voltage', 'sensor.foxinverter_invbatvolt', 'string', 'ha_entities',
         'Live battery voltage entity (V) — used for accurate kW to amps conversion')
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM system_settings
        WHERE `key` IN (
            'force_charge_threshold_kw',
            'battery_voltage_v',
            'ha_entity_charge_rate',
            'ha_entity_battery_voltage'
        )
    """)
