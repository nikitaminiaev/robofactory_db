import uuid
from sqlalchemy import Column, Text, ForeignKey, UUID
from sqlalchemy import DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.types import JSON

from .base import Base
from .associations import module_boundary

class ModuleBoundary(Base):
    __tablename__ = "module_boundaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interface_id_in = Column(UUID(as_uuid=True), ForeignKey('interface_objects.id'))
    interface_id_out = Column(UUID(as_uuid=True), ForeignKey('interface_objects.id'))
    stream_id = Column(UUID(as_uuid=True), ForeignKey('streams.id'))
    coordinates = Column(JSON, nullable=True)
    ttx = Column(Text, nullable=True)

    interface_in = relationship("InterfaceObject", foreign_keys=[interface_id_in])
    interface_out = relationship("InterfaceObject", foreign_keys=[interface_id_out])
    stream = relationship("Stream")
    
    modules = relationship(
        "Module",
        secondary=module_boundary,
        back_populates="boundaries"
    )

    created_ts = Column(DateTime(timezone=True), server_default=func.now())
    updated_ts = Column(DateTime(timezone=True), onupdate=func.now())

    def __str__(self):
        return f"ModuleBoundary(id={self.id!r})" 