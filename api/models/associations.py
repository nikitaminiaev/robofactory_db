from sqlalchemy import Column, ForeignKey, Table, UUID, JSON, String, Text, DateTime
from sqlalchemy.sql import func
from .base import Base
from .module_role import ModuleRole

# Связь родитель-потомок для модулей с координатами
parent_child_module = Table(
    'parent_child_module', Base.metadata,
    Column('parent_id', UUID(as_uuid=True), ForeignKey('modules.id'), primary_key=True),
    Column('child_id', UUID(as_uuid=True), ForeignKey('modules.id'), primary_key=True),
    Column('coordinates', JSON, nullable=True),  # Координаты XYZ и три угла
    Column('role_id', UUID(as_uuid=True), ForeignKey('module_roles.id'), nullable=True),
)

# Связь модулей и потоков
module_stream = Table(
    'module_stream', Base.metadata,
    Column('module_id', UUID(as_uuid=True), ForeignKey('modules.id'), primary_key=True),
    Column('stream_id', UUID(as_uuid=True), ForeignKey('streams.id'), primary_key=True)
)

# Связь модулей и платформ
module_platform = Table(
    'module_platform', Base.metadata,
    Column('module_id', UUID(as_uuid=True), ForeignKey('modules.id'), primary_key=True),
    Column('platform_id', UUID(as_uuid=True), ForeignKey('platforms.id'), primary_key=True)
)

# Связь модулей и module_boundaries объектов
module_boundary = Table(
    'module_boundary', Base.metadata,
    Column('module_id', UUID(as_uuid=True), ForeignKey('modules.id'), primary_key=True),
    Column('boundary_id', UUID(as_uuid=True), ForeignKey('module_boundaries.id'), primary_key=True)
) 