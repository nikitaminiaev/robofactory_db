import uuid
from sqlalchemy import Column, UUID, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base
from .associations import module_role_assignment


class ModuleRole(Base):
    __tablename__ = "module_roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_ts = Column(DateTime(timezone=True), server_default=func.now())

    modules = relationship("Module", secondary=module_role_assignment, back_populates="roles")
    ports = relationship("RolePort", back_populates="role", cascade="all, delete-orphan")