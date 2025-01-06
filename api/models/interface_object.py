import uuid
from typing import List

from sqlalchemy import Column, Text, JSON, DateTime, func, UUID
# from sqlalchemy.orm import relationship, Mapped

# from .module import Module
from .base import Base


class InterfaceObject(Base):
    __tablename__ = "interface_objects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # basic_objects: Mapped[List["Module"]] = relationship()
    coordinates = Column(JSON, nullable=True)  # Координаты XYZ и три угла
    description = Column(Text, nullable=True)
    ttx = Column(Text, nullable=True)

    created_ts = Column(DateTime(timezone=True), server_default=func.now())
    updated_ts = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return str(self)

    def __str__(self):
        return f"InterfaceObject(id={self.id!r})"
