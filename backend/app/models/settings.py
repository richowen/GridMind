"""ORM model for system_settings table. Key-value store for all runtime configuration."""

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.sql import func

from app.database import Base


class SystemSetting(Base):
    __tablename__ = "system_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    value_type = Column(String(20), default="string")  # 'string', 'float', 'int', 'bool'
    category = Column(String(50), nullable=False)       # 'battery', 'ha', 'octopus', etc.
    description = Column(Text)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
