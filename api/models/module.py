import uuid
from typing import Optional, List, Dict
from sqlalchemy import DateTime, ForeignKey, UUID, Boolean
from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from enum import Enum
from sqlalchemy import Enum as SQLAlchemyEnum

from .base import Base
from .bounding_contour import BoundingContour
from .associations import parent_child_module, module_stream, module_platform, module_boundary


class ModuleStatus(str, Enum):
    SKETCH = "эскиз"
    PROTOTYPE = "прототип"
    RELEASE = "релиз"


class Module(Base):
    __tablename__ = "modules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=False, nullable=False, index=True)
    abbreviation = Column(String, nullable=True)
    author = Column(String, nullable=False, server_default=func.user())
    description = Column(Text, nullable=True)  # Пояснительная записка
    ttx = Column(Text, nullable=True)
    version = Column(String, nullable=True)
    implementation = Column(String, nullable=True)  # Исполнение
    status = Column(SQLAlchemyEnum(ModuleStatus), nullable=False)
    is_lts = Column(Boolean, default=False)

    # Связи с другими таблицами
    service_id = Column(UUID(as_uuid=True), ForeignKey('services.id'), nullable=True)
    service: Mapped["Service"] = relationship(back_populates="modules")
    interface_object_id: Mapped[UUID] = mapped_column(ForeignKey("interface_objects.id"), nullable=True)
    bounding_contour: Mapped["BoundingContour"] = relationship(back_populates="module", uselist=False)

    # Связь parent-child с координатами
    children = relationship(
        "Module",
        secondary=parent_child_module,
        primaryjoin=id == parent_child_module.c.parent_id,
        secondaryjoin=id == parent_child_module.c.child_id,
        back_populates="parents"
    )
    parents = relationship(
        "Module",
        secondary=parent_child_module,
        primaryjoin=id == parent_child_module.c.child_id,
        secondaryjoin=id == parent_child_module.c.parent_id,
        back_populates="children"
    )

    streams = relationship(
        "Stream",
        secondary=module_stream,
        back_populates="modules"
    )

    platforms = relationship(
        "Platform",
        secondary=module_platform,
    )

    boundaries = relationship(
        "ModuleBoundary",
        secondary=module_boundary,
        back_populates="modules"
    )

    created_ts = Column(DateTime(timezone=True), server_default=func.now())
    updated_ts = Column(DateTime(timezone=True), onupdate=func.now())

    @classmethod
    def create(
            cls,
            name: str,
            author: str,
            description: Optional[str] = None,
            interface_object_id: UUID = None,
            children: Optional[List["Module"]] = None,
            parents: Optional[List["Module"]] = None,
            status: ModuleStatus = ModuleStatus.SKETCH
    ) -> "Module":
        """
        Factory method for creating a Module instance.
        """
        instance = cls(
            name=name,
            author=author,
            description=description,
            interface_object_id=interface_object_id,
            status=status,
        )

        # Add children and parents if provided
        if children:
            instance.children.extend(children)
        if parents:
            instance.parents.extend(parents)

        return instance

    def __repr__(self) -> str:
        return str(self)

    def __str__(self):
        return f"Module(id={self.id!r}, name={self.name!r}, author={self.author!r})"

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "abbreviation": self.abbreviation,
            "author": self.author,
            "description": self.description,
            "ttx": self.ttx,
            "version": self.version,
            "implementation": self.implementation,
            "status": self.status.value if self.status else None,
            "is_lts": self.is_lts,
            "children": [{"id": str(child.id)} for child in self.children],
            "parents": [{"id": str(parent.id)} for parent in self.parents],
            "created_ts": self.created_ts.isoformat() if self.created_ts else None,
            "updated_ts": self.updated_ts.isoformat() if self.updated_ts else None,
            "boundaries": [
                {
                    "id": str(boundary.id),
                    "coordinates": boundary.coordinates,
                    "interface_in": str(boundary.interface_id_in),
                    "interface_out": str(boundary.interface_id_out),
                    "stream_id": str(boundary.stream_id)
                } for boundary in self.boundaries
            ],
        }
