from sqlalchemy import String, Integer, Column, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func

from .base import Base


class AssemblyUnit(Base):
    __tablename__ = "assembly_units"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    number = Column(String(100), nullable=False, unique=True)
    assembly_unit_data = Column(JSON, nullable=True)

    product_id = Column(Integer, ForeignKey("products.id"))

    created_ts = Column(DateTime(timezone=True), server_default=func.now())
    updated_ts = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return str(self)

    def __str__(self):
        return f"AssemblyUnit(id={self.id!r}, name={self.name!r})"
