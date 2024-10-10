import uuid

from sqlalchemy import Column, JSON
from sqlalchemy import ForeignKey, Boolean, DateTime, func, UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base import Base


class BoundingContour(Base):
    __tablename__ = "bounding_contours"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Связь с BasicObject (1 к 1)
    basic_object_id: Mapped[UUID] = mapped_column(ForeignKey("basic_objects.id"), unique=True)
    basic_object: Mapped["BasicObject"] = relationship(back_populates="bounding_contour")

    is_assembly = Column(Boolean, nullable=False)
    brep_files = Column(JSON, nullable=True)  # Список BREP файлов или ссылок на них
    parent_id = Column(UUID(as_uuid=True), ForeignKey('bounding_contours.id'), nullable=True)
    parent = relationship("BoundingContour", remote_side=[id])

    created_ts = Column(DateTime(timezone=True), server_default=func.now())
    updated_ts = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return str(self)

    def __str__(self):
        return f"BoundingContour(id={self.id!r}, is_assembly={self.is_assembly!r})"

    def to_dict(self):
        return {
            "id": str(self.id),
            "basic_object_id": str(self.basic_object_id) if self.basic_object_id else None,
            "is_assembly": self.is_assembly,
            "brep_files": self.brep_files,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "created_ts": self.created_ts.isoformat() if self.created_ts else None,
            "updated_ts": self.updated_ts.isoformat() if self.updated_ts else None,
        }