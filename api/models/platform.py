import uuid
from sqlalchemy import Column, Text, DateTime, UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .base import Base
from .associations import module_platform

class Platform(Base):
    __tablename__ = "platforms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    description = Column(Text, nullable=True)
    ttx = Column(Text, nullable=True)
    
  
    services = relationship("Service", back_populates="platform")

    created_ts = Column(DateTime(timezone=True), server_default=func.now())
    updated_ts = Column(DateTime(timezone=True), onupdate=func.now())

    def __str__(self):
        return f"Platform(id={self.id!r})" 