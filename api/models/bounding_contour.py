from sqlalchemy import ForeignKey, Boolean
from sqlalchemy import Integer, Column, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column

from . import BasicObject
from .base import Base


class BoundingContour(Base):
    __tablename__ = "bounding_contours"

    id = Column(Integer, primary_key=True)


    # Связь с BasicObject (1 к 1)
    basic_object_id: Mapped[int] = mapped_column(ForeignKey("basic_objects.id"))
    basic_object: Mapped["BasicObject"] = relationship(back_populates="bounding_contour")

    is_assembly = Column(Boolean, nullable=False)
    brep_files = Column(JSON, nullable=True)  # Список BREP файлов или ссылок на них
    parent_id = Column(Integer, ForeignKey('bounding_contours.id'), nullable=True)
    parent = relationship("BoundingContour", remote_side=[id])

    def __repr__(self) -> str:
        return str(self)

    def __str__(self):
        return f"BoundingContour(id={self.id!r}, is_assembly={self.is_assembly!r})"
