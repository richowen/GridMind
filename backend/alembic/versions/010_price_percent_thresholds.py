"""010 — Replace absolute price thresholds with percentage-based daily classification.

Instead of fixed p/kWh thresholds, prices are now classified relative to the
day's min/max range:
  - cheap_percent_threshold (default 33): bottom N% of the day's range = cheap
  - expensive_percent_threshold (default 67): top N% of the day's range = expensive

The old absolute settings (price_cheap_threshold, price_expensive_threshold) are
removed. price_negative_threshold is kept as an absolute value — negative prices
are always negative regardless of the day's range.

Revision ID: 010
Revises: 009
Create Date: 2026-03-20
"""

from alembic import op

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new percentage-based threshold settings.
    # INSERT IGNORE is MariaDB syntax — safe to re-run.
    # `key` and `value` are reserved words in MariaDB — backtick-quoted.
    op.execute("""
        INSERT IGNORE INTO system_settings (`key`, `value`, value_type, category, description) VALUES
        ('price_cheap_percent_threshold', '33', 'int', 'prices',
         'Prices in the bottom N% of the daily min-max range are classified as cheap'),
        ('price_expensive_percent_threshold', '67', 'int', 'prices',
         'Prices above N% of the daily min-max range are classified as expensive')
    """)

    # Remove the old absolute threshold settings — they are superseded by the
    # percentage-based approach. price_negative_threshold is kept (absolute).
    op.execute("""
        DELETE FROM system_settings
        WHERE `key` IN ('price_cheap_threshold', 'price_expensive_threshold')
    """)


def downgrade() -> None:
    # Restore the old absolute settings and remove the percentage ones.
    op.execute("""
        INSERT IGNORE INTO system_settings (`key`, `value`, value_type, category, description) VALUES
        ('price_cheap_threshold', '10', 'float', 'prices', 'Below this = cheap price (p/kWh)'),
        ('price_expensive_threshold', '25', 'float', 'prices', 'Above this = expensive price (p/kWh)')
    """)
    op.execute("""
        DELETE FROM system_settings
        WHERE `key` IN ('price_cheap_percent_threshold', 'price_expensive_percent_threshold')
    """)
