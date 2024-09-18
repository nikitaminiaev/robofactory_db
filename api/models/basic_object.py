from sqlalchemy import DateTime
from sqlalchemy import Integer, Column, String, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class BasicObject(Base):
    __tablename__ = "basic_objects"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    author = Column(String, nullable=False, server_default=func.user())  # Имя пользователя, создающего объект
    description = Column(Text, nullable=True)
    coordinates = Column(JSON, nullable=True)  # Координаты XYZ и три угла
    role = Column(Text, nullable=True)
    role_description = Column(Text, nullable=True)

    # Связь с InterfaceObject
    interface_objects = relationship("InterfaceObject", backref="basic_object")

    created_ts = Column(DateTime(timezone=True), server_default=func.now())
    updated_ts = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return str(self)

    def __str__(self):
        return f"BasicObject(id={self.id!r}, name={self.name!r}, author={self.author!r})"


# class BasicObject(Base):
#     __tablename__ = 'basic_objects'
#
#     id = Column(Integer, primary_key=True)
#     name = Column(String(255), nullable=False)
#     author = Column(String(100), nullable=False, default="")  # Автор ставится автоматически в приложении
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
#     explanatory_note = Column(Text, nullable=True)
#
#     file_path = Column(String(255), nullable=False)
#     link_type = Column(String(100), nullable=False)  # Тип ссылки для автоматической обработки
#
#     # Связи с другими таблицами
#     bounding_contours = relationship("BoundingContour", back_populates="basic_object", cascade="all, delete-orphan")
#     child_objects = relationship("ChildObject", back_populates="parent_object", cascade="all, delete-orphan")
#     interface_objects = relationship("InterfaceObject", back_populates="parent_object", cascade="all, delete-orphan")
#     connections = relationship("Connection", back_populates="parent_object", cascade="all, delete-orphan")
#     file_data = relationship("FileData", back_populates="parent_object", cascade="all, delete-orphan")
#
#     def __repr__(self):
#         return f"BasicObject(id={self.id}, name={self.name})"