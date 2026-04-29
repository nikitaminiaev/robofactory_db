from uuid import UUID
from typing import Optional, List

from sqlalchemy.orm import Session

from . import BaseRepository
from models import ModuleRole, Module
from models.associations import module_role_assignment


class RoleRepository(BaseRepository):
    def get_role_by_name(self, db: Session, name: str) -> Optional[ModuleRole]:
        return db.query(ModuleRole).filter(ModuleRole.name == name).first()

    def get_role_by_id(self, db: Session, role_id: UUID) -> Optional[ModuleRole]:
        return db.query(ModuleRole).filter(ModuleRole.id == role_id).first()

    def get_all_roles(self, db: Session) -> List[ModuleRole]:
        return db.query(ModuleRole).order_by(ModuleRole.name).all()

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
            self.add_role_to_module(db, module_id, role.id)
            db.commit()
            db.refresh(role)
            return role