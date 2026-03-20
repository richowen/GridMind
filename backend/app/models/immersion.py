"""ORM models for immersion_devices, immersion_smart_rules, temperature_targets tables."""

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Index, Integer, String, Text, Time,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ImmersionDevice(Base):
    __tablename__ = "immersion_devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    switch_entity_id = Column(String(150), nullable=False)
    temp_sensor_entity_id = Column(String(150))
    is_enabled = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    # Tracks the last switch state GridMind commanded to HA.
    # NULL = GridMind has never commanded this device (skip external-change detection).
    last_commanded_state = Column(Boolean, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    smart_rules = relationship("ImmersionSmartRule", back_populates="device", cascade="all, delete-orphan")
    temp_targets = relationship("TemperatureTarget", back_populates="device", cascade="all, delete-orphan")
    overrides = relationship("ManualOverride", back_populates="device")


class ImmersionSmartRule(Base):
    __tablename__ = "immersion_smart_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    immersion_id = Column(Integer, ForeignKey("immersion_devices.id", ondelete="CASCADE"), nullable=False)
    rule_name = Column(String(100), nullable=False)
    is_enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=10)
    action = Column(String(10), nullable=False)       # 'ON' or 'OFF'
    logic_operator = Column(String(3), default="AND") # 'AND' or 'OR'

    price_enabled = Column(Boolean, default=False)
    price_operator = Column(String(5))
    price_threshold_pence = Column(Float)

    soc_enabled = Column(Boolean, default=False)
    soc_operator = Column(String(5))
    soc_threshold_percent = Column(Float)

    solar_enabled = Column(Boolean, default=False)
    solar_operator = Column(String(5))
    solar_threshold_kw = Column(Float)

    temp_enabled = Column(Boolean, default=False)
    temp_operator = Column(String(5))
    temp_threshold_c = Column(Float)

    time_enabled = Column(Boolean, default=False)
    time_start = Column(Time)
    time_end = Column(Time)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    device = relationship("ImmersionDevice", back_populates="smart_rules")

    __table_args__ = (
        Index("idx_device_priority", "immersion_id", "is_enabled", "priority"),
    )


class TemperatureTarget(Base):
    __tablename__ = "temperature_targets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    immersion_id = Column(Integer, ForeignKey("immersion_devices.id", ondelete="CASCADE"), nullable=False)
    target_name = Column(String(100), nullable=False)
    target_temp_c = Column(Float, nullable=False)
    target_time = Column(Time, nullable=False)
    days_of_week = Column(String(20), nullable=False)  # e.g. '0,1,2,3,4'
    heating_rate_c_per_hour = Column(Float, default=5.0)
    buffer_minutes = Column(Integer, default=30)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    device = relationship("ImmersionDevice", back_populates="temp_targets")
