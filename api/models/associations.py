from sqlalchemy import Column, ForeignKey, Table, UUID, JSON, text
from .base import Base

module_role_assignment = Table(
    'module_role_assignment', Base.metadata,
    Column('module_id', UUID(as_uuid=True), ForeignKey('modules.id'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('module_roles.id'), primary_key=True),
)

# Связь родитель-потомок для модулей с координатами.
# Суррогатный PK id позволяет иметь несколько записей с одной парой
# (parent_id, child_id) — для случаев, когда один дочерний модуль
# размещён в родителе несколько раз с разными координатами.
parent_child_module = Table(
    'parent_child_module', Base.metadata,
    Column('id', UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()')),
    Column('parent_id', UUID(as_uuid=True), ForeignKey('modules.id'), nullable=False),
    Column('child_id', UUID(as_uuid=True), ForeignKey('modules.id'), nullable=False),
    Column('coordinates', JSON, nullable=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('module_roles.id'), nullable=True),
)

parent_child_module_role_assignment = Table(
    'parent_child_module_role_assignment', Base.metadata,
    Column('parent_child_module_id', UUID(as_uuid=True), ForeignKey('parent_child_module.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('module_roles.id', ondelete='CASCADE'), primary_key=True),
)

# Связь модулей и потоков
module_stream = Table(
    'module_stream', Base.metadata,
    Column('module_id', UUID(as_uuid=True), ForeignKey('modules.id'), primary_key=True),
    Column('stream_id', UUID(as_uuid=True), ForeignKey('streams.id'), primary_key=True)
)

module_role_stream = Table(
    'module_role_stream', Base.metadata,
    Column('module_id', UUID(as_uuid=True), ForeignKey('modules.id', ondelete='CASCADE'), primary_key=True),
    Column('source_role_id', UUID(as_uuid=True), ForeignKey('module_roles.id', ondelete='CASCADE'), primary_key=True),
    Column('target_role_id', UUID(as_uuid=True), ForeignKey('module_roles.id', ondelete='CASCADE'), primary_key=True),
    Column('stream_id', UUID(as_uuid=True), ForeignKey('streams.id', ondelete='CASCADE'), primary_key=True),
    Column('source_port_id', UUID(as_uuid=True), ForeignKey('role_ports.id', ondelete='SET NULL'), nullable=True),
    Column('target_port_id', UUID(as_uuid=True), ForeignKey('role_ports.id', ondelete='SET NULL'), nullable=True),
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