import uuid
from sqlalchemy import Column, Text, DateTime, UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .base import Base
from .associations import module_stream

class Stream(Base):
    __tablename__ = "streams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    description = Column(Text, nullable=True)
    
    modules = relationship(
        "Module",
        secondary=module_stream,
        back_populates="streams"
    )

    created_ts = Column(DateTime(timezone=True), server_default=func.now())
    updated_ts = Column(DateTime(timezone=True), onupdate=func.now())

    def __str__(self):
        return f"Stream(id={self.id!r})" 