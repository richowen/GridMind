"""ORM model for electricity_prices table. Stores Octopus Agile half-hourly prices."""

from sqlalchemy import Column, DateTime, Float, Index, Integer, String

from app.database import Base


class ElectricityPrice(Base):
    __tablename__ = "electricity_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime, nullable=False)
    price_pence = Column(Float, nullable=False)
    classification = Column(String(20))  # 'negative', 'cheap', 'normal', 'expensive'

    __table_args__ = (
        Index("idx_valid_from", "valid_from"),
        Index("idx_valid_to", "valid_to"),
    )
