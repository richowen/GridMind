"""ORM models for optimization_results and system_states tables."""

from sqlalchemy import Boolean, Column, DateTime, Float, Index, Integer, String, Text

from app.database import Base


class OptimizationResult(Base):
    __tablename__ = "optimization_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False)
    current_soc = Column(Float)
    current_solar_kw = Column(Float)
    current_price_pence = Column(Float)
    recommended_mode = Column(String(50))
    recommended_discharge_current = Column(Integer)
    optimization_status = Column(String(20))
    optimization_time_ms = Column(Float)
    objective_value = Column(Float)
    decision_reason = Column(Text)
    next_action_time = Column(DateTime)  # Populated with next scheduled run time

    __table_args__ = (Index("idx_opt_timestamp", "timestamp"),)


class SystemState(Base):
    __tablename__ = "system_states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False)
    battery_soc = Column(Float)
    battery_mode = Column(String(50))
    solar_power_kw = Column(Float)
    solar_forecast_today_kwh = Column(Float)
    solar_forecast_next_hour_kw = Column(Float)  # From ha_entity_solar_forecast_1hr
    current_price_pence = Column(Float)
    # Note: immersion_main_on / immersion_lucy_on removed — use immersion_states
    # InfluxDB measurement (write_immersion_state) for per-device state logging.

    __table_args__ = (Index("idx_state_timestamp", "timestamp"),)
