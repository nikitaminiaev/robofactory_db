import uuid
from sqlalchemy import Column, Text, ForeignKey, UUID, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .base import Base

class ModuleUpdateReason(Base):
    __tablename__ = "reasons_modules_updating"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    old_module_id = Column(UUID(as_uuid=True), ForeignKey('modules.id'), nullable=False)
    new_module_id = Column(UUID(as_uuid=True), ForeignKey('modules.id'), nullable=False)
    reason = Column(Text, nullable=False)
    
    old_module = relationship("Module", foreign_keys=[old_module_id])
    new_module = relationship("Module", foreign_keys=[new_module_id])

    created_ts = Column(DateTime(timezone=True), server_default=func.now())

    def __str__(self):
        return f"ModuleUpdateReason(id={self.id!r})" 