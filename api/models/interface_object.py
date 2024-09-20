from typing import List

from sqlalchemy import Column, Integer, Text, JSON
from sqlalchemy.orm import relationship, Mapped

from . import BasicObject
from .base import Base


class InterfaceObject(Base):
    __tablename__ = "interface_objects"

    id = Column(Integer, primary_key=True)
    basic_objects: Mapped[List["BasicObject"]] = relationship()
    coordinates = Column(JSON, nullable=True)  # Координаты XYZ и три угла
    description = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return str(self)

    def __str__(self):
        return f"InterfaceObject(id={self.id!r})"
