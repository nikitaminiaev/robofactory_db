import uuid

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class InterfaceMapping(Base):
    __tablename__ = "interface_mappings"
    __table_args__ = (
        UniqueConstraint("module_id", "role_port_id", "interface_id", name="uq_interface_mappings_module_port_interface"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    module_id = Column(UUID(as_uuid=True), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False)
    role_port_id = Column(UUID(as_uuid=True), ForeignKey("role_ports.id", ondelete="CASCADE"), nullable=False)
    interface_id = Column(UUID(as_uuid=True), ForeignKey("interface_objects.id", ondelete="CASCADE"), nullable=False)

    module = relationship("Module")
    role_port = relationship("RolePort")
    interface = relationship("InterfaceObject")

    created_ts = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return str(self)

    def __str__(self):
        return f"InterfaceMapping(id={self.id!r})"
