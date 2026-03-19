"""ORM model for manual_overrides table. Tracks user-initiated immersion overrides."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ManualOverride(Base):
    __tablename__ = "manual_overrides"

    id = Column(Integer, primary_key=True, autoincrement=True)
    immersion_id = Column(Integer, ForeignKey("immersion_devices.id"), nullable=False)
    immersion_name = Column(String(50), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    desired_state = Column(Boolean, nullable=False)
    source = Column(String(50), default="user")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)
    cleared_at = Column(DateTime)
    cleared_by = Column(String(50))

    device = relationship("ImmersionDevice", back_populates="overrides")

    __table_args__ = (
        Index("idx_active_immersion", "immersion_id", "is_active", "expires_at"),
    )
