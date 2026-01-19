import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, UUID, String, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    from .module import Module


class ModuleVersion(Base):
    __tablename__ = "module_versions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    module_id: Mapped[UUID] = mapped_column(ForeignKey("modules.id"))
    version_number: Mapped[str] = mapped_column(String)
    commit_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(Text)
    created_ts: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    module: Mapped["Module"] = relationship(back_populates="versions")