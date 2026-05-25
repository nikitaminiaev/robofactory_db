import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, UniqueConstraint, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class RolePort(Base):
    __tablename__ = "role_ports"
    __table_args__ = (UniqueConstraint("role_id", "name", name="uq_role_ports_role_id_name"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID(as_uuid=True), ForeignKey("module_roles.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("role_ports.id", ondelete="CASCADE"), nullable=True)
    name = Column(String, nullable=False)
    direction = Column(String, nullable=False, default="bidirectional")
    description = Column(Text, nullable=True)
    ttx = Column(Text, nullable=True)
    created_ts = Column(DateTime(timezone=True), server_default=func.now())
    updated_ts = Column(DateTime(timezone=True), onupdate=func.now())

    role = relationship("ModuleRole", back_populates="ports")
    parent = relationship("RolePort", remote_side=[id], back_populates="children")
    children = relationship("RolePort", back_populates="parent", cascade="all, delete-orphan")
