from sqlalchemy import Integer, Column, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from .base import Base


class CadAspect(Base):
    __tablename__ = "cad_aspects"

    id = Column(Integer, primary_key=True)
    cad_data = Column(JSON, nullable=True)

    part_id = Column(Integer, ForeignKey('parts.id'), unique=True, nullable=True)
    part = relationship("Part", backref=backref("parts", uselist=False))

    assembly_unit_id = Column(Integer, ForeignKey('assembly_units.id'), unique=True, nullable=True)
    assembly_unit = relationship("AssemblyUnit", backref=backref("assembly_units", uselist=False))

    product_id = Column(Integer, ForeignKey('products.id'), unique=True, nullable=True)
    product = relationship("Product", backref=backref("products", uselist=False))

    created_ts = Column(DateTime(timezone=True), server_default=func.now())
    updated_ts = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return str(self)

    def __str__(self):
        return f"PartCad(id={self.id!r}, creation_date={self.created_ts!r}, " + \
               f"update_date={self.updated_ts!r}, geometry_data={self.cad_data!r})"
