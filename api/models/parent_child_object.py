from sqlalchemy import ForeignKey
from sqlalchemy import Integer, Column
from sqlalchemy.orm import relationship

from .base import Base


class ParentChildObject(Base):
    __tablename__ = "parent_child_objects"

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('basic_objects.id'), nullable=False)
    child_id = Column(Integer, ForeignKey('basic_objects.id'), nullable=False)

    parent = relationship("BasicObject", foreign_keys=[parent_id], backref="child_relationships")
    child = relationship("BasicObject", foreign_keys=[child_id], backref="parent_relationships")

    def __repr__(self) -> str:
        return str(self)

    def __str__(self):
        return f"ParentChildObject(id={self.id!r}, parent_id={self.parent_id!r}, child_id={self.child_id!r})"
