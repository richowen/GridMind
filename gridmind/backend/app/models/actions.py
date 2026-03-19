"""ORM model for system_actions table. Audit log of every Home Assistant call made."""

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class SystemAction(Base):
    __tablename__ = "system_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    action_type = Column(String(50), nullable=False)  # 'battery_mode', 'discharge_current', 'immersion'
    entity_id = Column(String(150), nullable=False)
    old_value = Column(String(100))
    new_value = Column(String(100), nullable=False)
    source = Column(String(50), nullable=False)  # 'optimizer', 'smart_rule', 'manual_override', etc.
    reason = Column(Text)
    success = Column(Boolean, default=True)

    __table_args__ = (
        Index("idx_action_timestamp", "timestamp"),
        Index("idx_action_type", "action_type"),
        Index("idx_action_entity", "entity_id"),
    )
