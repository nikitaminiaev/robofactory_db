from sqlalchemy import String, Integer, Column
from .base import Base


class PartCad(Base):
    __tablename__ = "parts_cad"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    cad_mass = Column(Integer, nullable=False)

    def __repr__(self) -> str:
        return str(self)

    def __str__(self):
        return f"PartCad(id={self.id!r}, name={self.name!r}, cad_mass={self.name!r})"
