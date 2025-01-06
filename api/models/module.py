import uuid
from typing import Optional, List, Dict
from sqlalchemy import DateTime, ForeignKey, UUID, Boolean
from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from enum import Enum

from .base import Base
from .bounding_contour import BoundingContour
from .associations import parent_child_module, module_stream, module_platform, module_interface, module_boundary

class ModuleStatus(Enum):
    SKETCH = "эскиз"
    PROTOTYPE = "прототип"
    RELEASE = "релиз"

class Module(Base):
    __tablename__ = "modules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    abbreviation = Column(String, nullable=True)
    author = Column(String, nullable=False, server_default=func.user())
    description = Column(Text, nullable=True)  # Пояснительная записка
    ttx = Column(Text, nullable=True)
    version = Column(String, nullable=True)
    implementation = Column(String, nullable=True)  # Исполнение
    status = Column(Enum(ModuleStatus), nullable=False)
    is_lts = Column(Boolean, default=False)
    
    # Связи с другими таблицами
    service_id = Column(UUID(as_uuid=True), ForeignKey('services.id'), nullable=True)
    bounding_contour: Mapped["BoundingContour"] = relationship(back_populates="basic_object", uselist=False)

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
        back_populates="modules"
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
            coordinates: Optional[Dict] = None,
            role: Optional[str] = None,
            role_description: Optional[str] = None,
            interface_object_id: UUID = None,
            children: Optional[List["Module"]] = None,
            parents: Optional[List["Module"]] = None
    ) -> "Module":
        """
        Factory method for creating a Module instance.
        """
        instance = cls(
            name=name,
            author=author,
            description=description,
            coordinates=coordinates,
            role=role,
            role_description=role_description,
            interface_object_id=interface_object_id,
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
            "children": [
                {
                    "id": str(child.id),
                    "coordinates": self.get_child_coordinates(child.id)
                } for child in self.children
            ],
            "parents": [
                {
                    "id": str(parent.id),
                    "coordinates": self.get_parent_coordinates(parent.id)
                } for parent in self.parents
            ],
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

    def get_child_coordinates(self, child_id):
        """Получить координаты для конкретного дочернего модуля"""
        result = db.session.query(parent_child_module.c.coordinates).filter(
            parent_child_module.c.parent_id == self.id,
            parent_child_module.c.child_id == child_id
        ).first()
        return result[0] if result else None

    def get_parent_coordinates(self, parent_id):
        """Получить координаты для конкретного родительского модуля"""
        result = db.session.query(parent_child_module.c.coordinates).filter(
            parent_child_module.c.child_id == self.id,
            parent_child_module.c.parent_id == parent_id
        ).first()
        return result[0] if result else None