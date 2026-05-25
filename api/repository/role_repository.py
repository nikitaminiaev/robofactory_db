from uuid import UUID
from typing import Any, Optional, List, cast

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, aliased

from . import BaseRepository
from models import ModuleRole, Module, RolePort, Stream
from models.associations import (
    module_role_assignment,
    module_role_stream,
    parent_child_module,
    parent_child_module_role_assignment,
)


class RoleRepository(BaseRepository):
    VALID_PORT_DIRECTIONS = {"input", "output", "bidirectional"}

    def get_role_by_name(self, db: Session, name: str) -> Optional[ModuleRole]:
        return db.query(ModuleRole).filter(ModuleRole.name == name).first()

    def get_role_by_id(self, db: Session, role_id: UUID) -> Optional[ModuleRole]:
        return db.query(ModuleRole).filter(ModuleRole.id == role_id).first()

    def get_all_roles(self, db: Session) -> List[ModuleRole]:
        return db.query(ModuleRole).order_by(ModuleRole.name).all()

    def search_roles(self, query: Optional[str] = None, limit: int = 20) -> List[dict]:
        with self.db_session.session() as db:
            stmt = db.query(ModuleRole).order_by(ModuleRole.name)
            if query:
                stmt = stmt.filter(ModuleRole.name.ilike(f"%{query}%"))
            roles = stmt.limit(limit).all()

        return [
            {"id": str(role.id), "name": role.name, "description": role.description}
            for role in roles
        ]

    def create_role(self, db: Session, name: str, description: Optional[str] = None) -> ModuleRole:
        role = ModuleRole(name=name, description=description)
        db.add(role)
        db.flush()
        return role

    def get_or_create_role(self, db: Session, name: str, description: Optional[str] = None) -> ModuleRole:
        existing_role = self.get_role_by_name(db, name)
        if existing_role:
            return existing_role
        return self.create_role(db, name, description)

    def add_role_to_module(self, db: Session, module_id: UUID, role_id: UUID) -> None:
        existing = db.execute(
            module_role_assignment.select().where(
                module_role_assignment.c.module_id == module_id,
                module_role_assignment.c.role_id == role_id,
            )
        ).first()
        if existing:
            return
        db.execute(module_role_assignment.insert().values(module_id=module_id, role_id=role_id))
        db.flush()

    def remove_role_from_module(self, db: Session, module_id: UUID, role_id: UUID) -> None:
        child_link_ids = select(parent_child_module.c.id).where(
            parent_child_module.c.parent_id == module_id
        )
        db.execute(
            parent_child_module_role_assignment.delete().where(
                parent_child_module_role_assignment.c.parent_child_module_id.in_(child_link_ids),
                parent_child_module_role_assignment.c.role_id == role_id,
            )
        )
        db.execute(
            module_role_stream.delete().where(
                module_role_stream.c.module_id == module_id,
                or_(
                    module_role_stream.c.source_role_id == role_id,
                    module_role_stream.c.target_role_id == role_id,
                ),
            )
        )
        db.execute(
            module_role_assignment.delete().where(
                module_role_assignment.c.module_id == module_id,
                module_role_assignment.c.role_id == role_id,
            )
        )
        db.flush()

    def get_module_roles(self, db: Session, module_id: UUID) -> List[ModuleRole]:
        module = db.query(Module).filter(Module.id == module_id).first()
        if not module:
            return []
        return module.roles

    def get_role_details(self, role_id: UUID) -> Optional[dict]:
        with self.db_session.session() as db:
            role = self.get_role_by_id(db, role_id)
            if not role:
                return None

            role_obj = cast(Any, role)
            return {
                "id": str(role_obj.id),
                "name": role_obj.name,
                "description": role_obj.description,
                "created_ts": role_obj.created_ts.isoformat() if role_obj.created_ts else None,
                "ports": self.get_role_ports(db, role_id),
                "stream_usages": self.get_role_stream_usages(db, role_id),
            }

    def _port_to_dict(self, port: RolePort) -> dict:
        port_obj = cast(Any, port)
        return {
            "id": str(port_obj.id),
            "role_id": str(port_obj.role_id),
            "parent_id": str(port_obj.parent_id) if port_obj.parent_id else None,
            "name": port_obj.name,
            "direction": port_obj.direction,
            "description": port_obj.description,
            "ttx": port_obj.ttx,
            "created_ts": port_obj.created_ts.isoformat() if port_obj.created_ts else None,
            "updated_ts": port_obj.updated_ts.isoformat() if port_obj.updated_ts else None,
        }

    def get_role_ports(self, db: Session, role_id: UUID) -> List[dict]:
        ports = (
            db.query(RolePort)
            .filter(RolePort.role_id == role_id)
            .order_by(RolePort.name)
            .all()
        )
        return [self._port_to_dict(port) for port in ports]

    def get_role_port_by_id(self, db: Session, role_id: UUID, port_id: UUID) -> Optional[RolePort]:
        return (
            db.query(RolePort)
            .filter(RolePort.id == port_id, RolePort.role_id == role_id)
            .first()
        )

    def _normalize_port_direction(self, direction: Optional[str]) -> str:
        normalized = (direction or "bidirectional").strip()
        if normalized in self.VALID_PORT_DIRECTIONS:
            return normalized
        raise ValueError("Неверное направление порта")

    def _ensure_parent_port(
        self,
        db: Session,
        role_id: UUID,
        parent_id: Optional[UUID],
        port_id: Optional[UUID] = None,
    ) -> None:
        if parent_id is None:
            return
        if port_id is not None and parent_id == port_id:
            raise ValueError("Порт не может быть родителем самого себя")
        parent = self.get_role_port_by_id(db, role_id, parent_id)
        if parent:
            return
        raise ValueError("Родительский порт не найден у этой роли")

    def create_role_port(
        self,
        role_id: UUID,
        name: str,
        direction: Optional[str] = None,
        description: Optional[str] = None,
        ttx: Optional[str] = None,
        parent_id: Optional[UUID] = None,
    ) -> Optional[dict]:
        with self.db_session.session() as db:
            role = self.get_role_by_id(db, role_id)
            if not role:
                return None

            name = name.strip()
            if not name:
                raise ValueError("Название порта не может быть пустым")

            self._ensure_parent_port(db, role_id, parent_id)
            port = RolePort(
                role_id=role_id,
                parent_id=parent_id,
                name=name,
                direction=self._normalize_port_direction(direction),
                description=description,
                ttx=ttx,
            )
            db.add(port)
            db.commit()
            db.refresh(port)
            return self._port_to_dict(port)

    def update_role_port(
        self,
        role_id: UUID,
        port_id: UUID,
        name: str,
        direction: Optional[str] = None,
        description: Optional[str] = None,
        ttx: Optional[str] = None,
        parent_id: Optional[UUID] = None,
    ) -> Optional[dict]:
        with self.db_session.session() as db:
            port = self.get_role_port_by_id(db, role_id, port_id)
            if not port:
                return None

            name = name.strip()
            if not name:
                raise ValueError("Название порта не может быть пустым")

            self._ensure_parent_port(db, role_id, parent_id, port_id)
            port_obj = cast(Any, port)
            port_obj.name = name
            port_obj.direction = self._normalize_port_direction(direction)
            port_obj.description = description
            port_obj.ttx = ttx
            port_obj.parent_id = parent_id
            db.commit()
            db.refresh(port)
            return self._port_to_dict(port)

    def delete_role_port(self, role_id: UUID, port_id: UUID) -> bool:
        with self.db_session.session() as db:
            port = self.get_role_port_by_id(db, role_id, port_id)
            if not port:
                return False
            db.delete(port)
            db.commit()
            return True

    def get_role_modules(self, db: Session, role_id: UUID) -> List[dict]:
        rows = db.execute(
            select(Module.id, Module.name, Module.description)
            .join(module_role_assignment, module_role_assignment.c.module_id == Module.id)
            .where(module_role_assignment.c.role_id == role_id)
            .order_by(Module.name)
        ).fetchall()

        return [
            {
                "id": str(row.id),
                "name": row.name,
                "description": row.description,
            }
            for row in rows
        ]

    def get_role_port_usages(self, db: Session, role_id: UUID) -> List[dict]:
        parent_module = aliased(Module)
        child_module = aliased(Module)
        rows = db.execute(
            select(
                parent_child_module.c.id.label("parent_child_module_id"),
                parent_module.id.label("parent_id"),
                parent_module.name.label("parent_name"),
                child_module.id.label("child_id"),
                child_module.name.label("child_name"),
            )
            .join(
                parent_child_module_role_assignment,
                parent_child_module_role_assignment.c.parent_child_module_id == parent_child_module.c.id,
            )
            .join(parent_module, parent_module.id == parent_child_module.c.parent_id)
            .join(child_module, child_module.id == parent_child_module.c.child_id)
            .where(parent_child_module_role_assignment.c.role_id == role_id)
            .order_by(parent_module.name, child_module.name)
        ).fetchall()

        return [
            {
                "parent_child_module_id": str(row.parent_child_module_id),
                "parent_id": str(row.parent_id),
                "parent_name": row.parent_name,
                "child_id": str(row.child_id),
                "child_name": row.child_name,
            }
            for row in rows
        ]

    def get_role_stream_usages(self, db: Session, role_id: UUID) -> List[dict]:
        source_role = aliased(ModuleRole)
        target_role = aliased(ModuleRole)
        source_port = aliased(RolePort)
        target_port = aliased(RolePort)
        rows = db.execute(
            select(
                Module.id.label("module_id"),
                Module.name.label("module_name"),
                module_role_stream.c.source_role_id,
                source_role.name.label("source_role_name"),
                module_role_stream.c.target_role_id,
                target_role.name.label("target_role_name"),
                module_role_stream.c.source_port_id,
                source_port.name.label("source_port_name"),
                module_role_stream.c.target_port_id,
                target_port.name.label("target_port_name"),
                Stream.id.label("stream_id"),
                Stream.name.label("stream_name"),
                Stream.description.label("stream_description"),
            )
            .join(Module, Module.id == module_role_stream.c.module_id)
            .join(source_role, source_role.id == module_role_stream.c.source_role_id)
            .join(target_role, target_role.id == module_role_stream.c.target_role_id)
            .outerjoin(source_port, source_port.id == module_role_stream.c.source_port_id)
            .outerjoin(target_port, target_port.id == module_role_stream.c.target_port_id)
            .join(Stream, Stream.id == module_role_stream.c.stream_id)
            .where(
                or_(
                    module_role_stream.c.source_role_id == role_id,
                    module_role_stream.c.target_role_id == role_id,
                )
            )
            .order_by(Module.name, Stream.name, source_role.name, target_role.name)
        ).fetchall()

        return [
            {
                "module_id": str(row.module_id),
                "module_name": row.module_name,
                "source_role_id": str(row.source_role_id),
                "source_role_name": row.source_role_name,
                "target_role_id": str(row.target_role_id),
                "target_role_name": row.target_role_name,
                "source_port_id": str(row.source_port_id) if row.source_port_id else None,
                "source_port_name": row.source_port_name,
                "target_port_id": str(row.target_port_id) if row.target_port_id else None,
                "target_port_name": row.target_port_name,
                "stream_id": str(row.stream_id),
                "stream_name": row.stream_name,
                "stream_description": row.stream_description,
            }
            for row in rows
        ]

    def update_role(self, role_id: UUID, name: str, description: Optional[str] = None) -> Optional[dict]:
        with self.db_session.session() as db:
            role = self.get_role_by_id(db, role_id)
            if not role:
                return None

            role_obj = cast(Any, role)
            role_obj.name = name
            role_obj.description = description
            db.commit()
            db.refresh(role)

            return {
                "id": str(role_obj.id),
                "name": role_obj.name,
                "description": role_obj.description,
                "created_ts": role_obj.created_ts.isoformat() if role_obj.created_ts else None,
            }

    def delete_role(self, role_id: UUID) -> bool:
        with self.db_session.session() as db:
            role = self.get_role_by_id(db, role_id)
            if not role:
                return False

            db.execute(
                module_role_stream.delete().where(
                    or_(
                        module_role_stream.c.source_role_id == role_id,
                        module_role_stream.c.target_role_id == role_id,
                    )
                )
            )
            db.execute(
                parent_child_module_role_assignment.delete().where(
                    parent_child_module_role_assignment.c.role_id == role_id
                )
            )
            db.execute(
                parent_child_module.update()
                .where(parent_child_module.c.role_id == role_id)
                .values(role_id=None)
            )
            db.execute(
                module_role_assignment.delete().where(
                    module_role_assignment.c.role_id == role_id
                )
            )
            db.delete(role)
            db.commit()
            return True

    # --- Методы с самостоятельным управлением сессией (для API эндпоинтов) ---

    def fetch_module_roles(self, module_id: UUID) -> List[ModuleRole]:
        with self.db_session.session() as db:
            return self.get_module_roles(db, module_id)

    def assign_role(self, module_id: UUID, role_id: UUID) -> None:
        with self.db_session.session() as db:
            self.add_role_to_module(db, module_id, role_id)
            db.commit()

    def unassign_role(self, module_id: UUID, role_id: UUID) -> None:
        with self.db_session.session() as db:
            self.remove_role_from_module(db, module_id, role_id)
            db.commit()

    def create_and_assign_role(self, module_id: UUID, name: str, description: Optional[str] = None) -> ModuleRole:
        with self.db_session.session() as db:
            role = self.get_or_create_role(db, name, description)
            self.add_role_to_module(db, module_id, cast(Any, role).id)
            db.commit()
            db.refresh(role)
            return role