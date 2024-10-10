import uuid
from sqlalchemy import DateTime, ForeignKey, Table, UUID
from sqlalchemy import Column, String, Text, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from .bounding_contour import BoundingContour
from .base import Base

parent_child_association = Table(
    'parent_child_association', Base.metadata,
    Column('parent_id', UUID(as_uuid=True), ForeignKey('basic_objects.id'), primary_key=True),
    Column('child_id', UUID(as_uuid=True), ForeignKey('basic_objects.id'), primary_key=True)
)

class BasicObject(Base):
    __tablename__ = "basic_objects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    author = Column(String, nullable=False, server_default=func.user())  # Имя пользователя, создающего объект
    description = Column(Text, nullable=True)
    coordinates = Column(JSON, nullable=True)  # Координаты XYZ и три угла
    role = Column(Text, nullable=True)
    role_description = Column(Text, nullable=True)

    # Связь с InterfaceObject (1 ко многим)
    interface_object_id: Mapped[UUID] = mapped_column(ForeignKey("interface_objects.id"), nullable=True)

    # Связь с BoundingContour (1 к 1)
    bounding_contour: Mapped["BoundingContour"] = relationship(back_populates="basic_object", uselist=False)

    # Связь многие ко многим с самим собой
    children = relationship(
        "BasicObject",
        secondary=parent_child_association,
        primaryjoin=id == parent_child_association.c.parent_id,
        secondaryjoin=id == parent_child_association.c.child_id,
        back_populates="parents"
    )
    parents = relationship(
        "BasicObject",
        secondary=parent_child_association,
        primaryjoin=id == parent_child_association.c.child_id,
        secondaryjoin=id == parent_child_association.c.parent_id,
        back_populates="children"
    )

    created_ts = Column(DateTime(timezone=True), server_default=func.now())
    updated_ts = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return str(self)

    def __str__(self):
        return f"BasicObject(id={self.id!r}, name={self.name!r}, author={self.author!r})"