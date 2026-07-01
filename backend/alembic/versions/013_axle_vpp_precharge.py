"""013 — Add Axle VPP pre-charge guarantee settings.

Revision ID: 013
Revises: 012
Create Date: 2026-07-01
"""

from alembic import op

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # INSERT IGNORE ensures seed rows are added without failing if they already exist.
    # `key` and `value` are reserved words in MariaDB — backtick-quote them in raw SQL.
    op.execute("""
        INSERT IGNORE INTO system_settings (`key`, `value`, value_type, category, description) VALUES
        ('axle_vpp_precharge_enabled', 'true', 'bool', 'optimization',
         'Guarantee battery is charged high enough to sustain full export for an upcoming VPP event'),
        ('axle_vpp_precharge_buffer_percent', '5.0', 'float', 'optimization',
         'Extra SOC % margin added on top of the calculated VPP pre-charge requirement')
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM system_settings
        WHERE `key` IN (
            'axle_vpp_precharge_enabled',
            'axle_vpp_precharge_buffer_percent'
        )
    """)
