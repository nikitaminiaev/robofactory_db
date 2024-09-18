from sqlalchemy import ForeignKey, Boolean
from sqlalchemy import Integer, Column, JSON
from sqlalchemy.orm import relationship, backref

from .base import Base


class BoundingContour(Base):
    __tablename__ = "bounding_contours"

    id = Column(Integer, primary_key=True)
    basic_object_id = Column(Integer, ForeignKey('basic_objects.id'), unique=True, nullable=False)
    basic_object = relationship("BasicObject", backref=backref("bounding_contour", uselist=False))

    is_assembly = Column(Boolean, nullable=False)
    brep_files = Column(JSON, nullable=True)  # Список BREP файлов или ссылок на них
    parent_id = Column(Integer, ForeignKey('bounding_contours.id'), nullable=True)
    parent = relationship("BoundingContour", remote_side=[id])

    def __repr__(self) -> str:
        return str(self)

    def __str__(self):
        return f"BoundingContour(id={self.id!r}, is_assembly={self.is_assembly!r})"
