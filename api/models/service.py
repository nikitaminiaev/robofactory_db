import uuid
from sqlalchemy import Column, Text, ForeignKey, UUID, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .base import Base

class Service(Base):
    __tablename__ = "services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    description = Column(Text, nullable=True)
    platform_id = Column(UUID(as_uuid=True), ForeignKey('platforms.id'), nullable=False)
    
    platform = relationship("Platform", back_populates="services")
    modules = relationship("Module", back_populates="service")

    created_ts = Column(DateTime(timezone=True), server_default=func.now())
    updated_ts = Column(DateTime(timezone=True), onupdate=func.now())

    def __str__(self):
        return f"Service(id={self.id!r})" 