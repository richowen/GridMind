"""009 — Add last_commanded_state to immersion_devices for external change detection.

Tracks the last switch state GridMind commanded to HA. If the current HA state
differs from this value (and no manual override is active), GridMind knows the
switch was changed externally and auto-creates a ManualOverride.

Also adds manual_override_auto_duration_minutes to system_settings.

Revision ID: 009
Revises: 008
Create Date: 2026-03-20
"""

from alembic import op
import sqlalchemy as sa

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add last_commanded_state to immersion_devices.
    # NULL means GridMind has never commanded this device — detection is skipped
    # until GridMind issues its first command, preventing false positives on first boot.
    op.add_column(
        "immersion_devices",
        sa.Column("last_commanded_state", sa.Boolean, nullable=True),
    )

    # Add configurable auto-override duration setting (default 120 minutes = 2 hours)
    op.execute(
        """
        INSERT INTO system_settings (key, value, description, category, updated_at)
        VALUES (
            'manual_override_auto_duration_minutes',
            '120',
            'Duration in minutes for auto-created overrides when an external HA state change is detected',
            'immersion',
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (key) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_column("immersion_devices", "last_commanded_state")
    op.execute(
        "DELETE FROM system_settings WHERE key = 'manual_override_auto_duration_minutes'"
    )
