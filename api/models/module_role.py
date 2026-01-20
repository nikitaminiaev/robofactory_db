import uuid
from sqlalchemy import Column, UUID, String, Text, DateTime
from sqlalchemy.sql import func

from .base import Base


class ModuleRole(Base):
    __tablename__ = "module_roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_ts = Column(DateTime(timezone=True), server_default=func.now()) 