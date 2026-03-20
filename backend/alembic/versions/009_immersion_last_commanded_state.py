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
from sqlalchemy import inspect

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # Add last_commanded_state to immersion_devices — idempotent via IF NOT EXISTS.
    # NULL means GridMind has never commanded this device — detection is skipped
    # until GridMind issues its first command, preventing false positives on first boot.
    # The first migration attempt partially succeeded (column was added) before the
    # INSERT failed, so IF NOT EXISTS prevents the duplicate-column error on retry.
    existing_cols = [c["name"] for c in inspector.get_columns("immersion_devices")]
    if "last_commanded_state" not in existing_cols:
        op.add_column(
            "immersion_devices",
            sa.Column("last_commanded_state", sa.Boolean, nullable=True),
        )

    # Add configurable auto-override duration setting (default 120 minutes = 2 hours).
    # Use INSERT IGNORE (MariaDB syntax) and backtick-quote `key` and `value` which
    # are reserved words in MariaDB — matches the pattern used in migration 006.
    op.execute(
        """
        INSERT IGNORE INTO system_settings (`key`, `value`, value_type, category, description)
        VALUES (
            'manual_override_auto_duration_minutes',
            '120',
            'int',
            'immersion',
            'Duration in minutes for auto-created overrides when an external HA state change is detected'
        )
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    existing_cols = [c["name"] for c in inspector.get_columns("immersion_devices")]
    if "last_commanded_state" in existing_cols:
        op.drop_column("immersion_devices", "last_commanded_state")

    op.execute(
        "DELETE FROM system_settings WHERE `key` = 'manual_override_auto_duration_minutes'"
    )
