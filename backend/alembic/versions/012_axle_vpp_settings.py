"""012 — Add Axle VPP integration settings.

Revision ID: 012
Revises: 011
Create Date: 2026-06-25
"""

from alembic import op

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # INSERT IGNORE ensures seed rows are added without failing if they already exist.
    # `key` and `value` are reserved words in MariaDB — backtick-quote them in raw SQL.
    op.execute("""
        INSERT IGNORE INTO system_settings (`key`, `value`, value_type, category, description) VALUES
        ('axle_vpp_enabled', 'false', 'bool', 'optimization', 'Enable Axle VPP Integration'),
        ('axle_vpp_token', '', 'string', 'optimization', 'Axle VPP API Bearer Token'),
        ('axle_vpp_export_price_pence', '100.0', 'float', 'optimization', 'Export rate in pence/kWh during active VPP event'),
        ('disable_immersion_during_vpp', 'true', 'bool', 'optimization', 'Disable immersion heaters during active VPP event')
    """)
    # Update battery_max_discharge_kw default raw total discharge capacity to 10.0 kW (vs 5.0 kW grid export limit)
    op.execute("UPDATE system_settings SET `value`='10.0' WHERE `key`='battery_max_discharge_kw'")


def downgrade() -> None:
    # Revert battery_max_discharge_kw
    op.execute("UPDATE system_settings SET `value`='5.0' WHERE `key`='battery_max_discharge_kw'")
    op.execute("""
        DELETE FROM system_settings
        WHERE `key` IN (
            'axle_vpp_enabled',
            'axle_vpp_token',
            'axle_vpp_export_price_pence',
            'disable_immersion_during_vpp'
        )
    """)
