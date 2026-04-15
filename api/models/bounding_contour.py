import uuid
from typing import Optional, Dict, TYPE_CHECKING

from sqlalchemy import Column, JSON
from sqlalchemy import ForeignKey, Boolean, DateTime, func, UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.mutable import MutableDict

if TYPE_CHECKING:
    from .module import Module

from .base import Base
from service.constants import resolve_brep_absolute_path

class BoundingContour(Base):
    __tablename__ = "bounding_contours"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Связь с Module (1 к 1)
    module_id: Mapped[UUID] = mapped_column(ForeignKey("modules.id"), unique=True)
    module: Mapped["Module"] = relationship(back_populates="bounding_contour")

    is_assembly = Column(Boolean, nullable=False)
    is_shell: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    brep_files: Mapped[Optional[Dict[str, str]]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=True
    )  # Ссылки на BREP файлы: имя -> относительный путь
    parent_id = Column(UUID(as_uuid=True), ForeignKey('bounding_contours.id'), nullable=True)
    parent = relationship("BoundingContour", remote_side=[id])

    created_ts = Column(DateTime(timezone=True), server_default=func.now())
    updated_ts = Column(DateTime(timezone=True), onupdate=func.now())

    @classmethod
    def create(cls, is_assembly: bool, brep_files: Optional[Dict[str, str]] = None,
                module_id: Optional[UUID] = None, parent_id: Optional[UUID] = None,
                is_shell: bool = False) -> "BoundingContour":
        """
        Factory method for creating a BoundingContour instance.
        """
        return cls(
            is_assembly=is_assembly,
            brep_files=brep_files or {},
            module_id=module_id,
            parent_id=parent_id,
            is_shell=is_shell
        )

    def __repr__(self) -> str:
        return str(self)

    def __str__(self):
        return f"BoundingContour(id={self.id!r}, is_assembly={self.is_assembly!r}, is_shell={self.is_shell!r})"

    def to_dict(self):
        # Читаем содержимое BREP файлов вместо возврата путей
        brep_files_content = {}
        if self.brep_files:
            for filename, relative_path in self.brep_files.items():
                try:
                    full_path = resolve_brep_absolute_path(relative_path)
                    if full_path.exists():
                        content = full_path.read_text()
                        # Всегда возвращаем brep_string если файл существует
                        if filename == 'brep_string':
                            brep_files_content['path'] = str(full_path)
                            brep_files_content['brep_string'] = content
                        else:
                            brep_files_content[filename] = content
                    else:
                        # Файл не существует - возвращаем только path
                        if filename == 'brep_string':
                            brep_files_content['path'] = str(full_path)
                            # brep_string не записываем - файл не существует
                        else:
                            brep_files_content[filename] = ""
                except Exception as e:
                    if filename == 'brep_string':
                        brep_files_content['path'] = None
                    else:
                        brep_files_content[filename] = ""

        return {
            "id": str(self.id),
            "module_id": str(self.module_id) if self.module_id else None,
            "is_assembly": self.is_assembly,
            "is_shell": self.is_shell,
            "brep_files": brep_files_content,  # Возвращаем содержимое файлов в формате, ожидаемом клиентом
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "created_ts": self.created_ts.isoformat() if self.created_ts else None,
            "updated_ts": self.updated_ts.isoformat() if self.updated_ts else None,
        }