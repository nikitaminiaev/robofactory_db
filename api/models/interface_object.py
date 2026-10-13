import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, JSON, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class InterfaceObject(Base):
    __tablename__ = "interface_objects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String, nullable=False, default="")
    direction = Column(String, nullable=False, default="bidirectional")
    physical_form = Column(String, nullable=True)
    parameters = Column(JSON, nullable=True)
    is_mandatory = Column(Boolean, default=True)
    is_service = Column(Boolean, default=False)

    module_id = Column(UUID(as_uuid=True), ForeignKey("modules.id", ondelete="SET NULL"), nullable=True)
    module = relationship("Module", back_populates="interfaces", foreign_keys=[module_id])

    coordinates = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    ttx = Column(Text, nullable=True)

    created_ts = Column(DateTime(timezone=True), server_default=func.now())
    updated_ts = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return str(self)

    def __str__(self):
        return f"InterfaceObject(id={self.id!r}, name={self.name!r})"
