from . import BaseRepository
from models import ModuleRole
from sqlalchemy.orm import Session
from typing import Optional


class RoleRepository(BaseRepository):
    def get_role_by_name(self, db: Session, name: str) -> Optional[ModuleRole]:
        """Получить роль по имени"""
        return db.query(ModuleRole).filter(ModuleRole.name == name).first()

    def create_role(self, db: Session, name: str, description: Optional[str] = None) -> ModuleRole:
        """Создать новую роль"""
        role = ModuleRole(
            name=name,
            description=description
        )
        db.add(role)
        db.flush()
        return role

    def get_or_create_role(self, db: Session, name: str, description: Optional[str] = None) -> ModuleRole:
        """Получить существующую роль или создать новую"""
        existing_role = self.get_role_by_name(db, name)
        if existing_role:
            return existing_role
        
        return self.create_role(db, name, description) 