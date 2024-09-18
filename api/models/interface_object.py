from sqlalchemy import Column, Integer, Text, ForeignKey, JSON

from .base import Base


class InterfaceObject(Base):
    __tablename__ = "interface_objects"

    id = Column(Integer, primary_key=True)
    basic_object_id = Column(Integer, ForeignKey('basic_objects.id'), nullable=False)
    coordinates = Column(JSON, nullable=True)  # Координаты XYZ и три угла
    description = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return str(self)

    def __str__(self):
        return f"InterfaceObject(id={self.id!r})"
