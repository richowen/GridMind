"""014 — Add heater stall Discord alert settings.

Revision ID: 014
Revises: 013
Create Date: 2026-09-02
"""

from alembic import op

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # INSERT IGNORE ensures seed rows are added without failing if they already exist.
    # `key` and `value` are reserved words in MariaDB — backtick-quote them in raw SQL.
    op.execute("""
        INSERT IGNORE INTO system_settings (`key`, `value`, value_type, category, description) VALUES
        ('discord_webhook_url', '', 'string', 'alerts', 'Discord webhook URL for system alerts'),
        ('heater_stall_alert_enabled', 'true', 'bool', 'alerts',
         'Alert via Discord if water temp does not rise while a temperature target is heating'),
        ('heater_stall_check_minutes', '20', 'int', 'alerts',
         'Minutes of temperature-target heating before checking for a stalled water temp'),
        ('heater_stall_min_rise_c', '0.5', 'float', 'alerts',
         'Minimum degC rise expected over the check window before flagging a stall')
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM system_settings
        WHERE `key` IN (
            'discord_webhook_url',
            'heater_stall_alert_enabled',
            'heater_stall_check_minutes',
            'heater_stall_min_rise_c'
        )
    """)
