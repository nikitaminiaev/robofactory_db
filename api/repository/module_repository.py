from uuid import UUID
from sqlalchemy.orm import joinedload
from . import BaseRepository
from models import Module
from models.associations import parent_child_module


class ModuleRepository(BaseRepository):
    def get_all_modules(self) -> list[Module]:
        with (self.db_session.session() as db):
            modules = db.query(Module).options(
                joinedload(Module.bounding_contour),
                joinedload(Module.children),
                joinedload(Module.parents),
                joinedload(Module.boundaries),
                joinedload(Module.streams),
                joinedload(Module.platforms)
            ).all()
        return modules

    def get_module(self, name: str) -> Module:
        with self.db_session.session() as db:
            module = db.query(Module).filter_by(name=name).first()
        return module

    def get_module_with_relations(self, name: str) -> Module:
        with self.db_session.session() as db:
            module = db.query(Module).options(
                joinedload(Module.bounding_contour),
                joinedload(Module.children),
                joinedload(Module.parents),
                joinedload(Module.boundaries),
                joinedload(Module.streams),
                joinedload(Module.platforms)
            ).filter_by(name=name).first()
        return module
    
    def get_module_by_id(self, id: UUID) -> Module:
        with self.db_session.session() as db:
            module = db.query(Module).filter_by(id=id).first()
        return module

    def get_module_for_update(self, id: UUID, db_session) -> Module:
        return db_session.query(Module).filter_by(id=id).first()

    def get_module_with_relations_by_id(self, id: UUID) -> Module:
        with self.db_session.session() as db:
            module = db.query(Module).options(
                joinedload(Module.bounding_contour),
                joinedload(Module.children),
                joinedload(Module.parents),
                joinedload(Module.boundaries),
                joinedload(Module.streams),
                joinedload(Module.platforms)
            ).filter_by(id=id).first()
        return module

    def get_child_coordinates(self, parent_id: UUID, child_id: UUID):
        return self._get_coordinates(parent_id, child_id, is_parent=True)

    def get_parent_coordinates(self, child_id: UUID, parent_id: UUID):
        return self._get_coordinates(child_id, parent_id, is_parent=False)

    def _get_coordinates(self, id1: UUID, id2: UUID, is_parent: bool = True):
        """
        Приватный метод для получения координат связи между модулями
        
        Args:
            id1: UUID первого модуля
            id2: UUID второго модуля
            is_parent: если True, то id1 - родитель, id2 - потомок
                      если False, то id1 - потомок, id2 - родитель
        """
        with self.db_session.session() as db:
            filters = [
                parent_child_module.c.parent_id == id2 if not is_parent else id1,
                parent_child_module.c.child_id == id1 if not is_parent else id2
            ]
            result = db.query(parent_child_module.c.coordinates).filter(*filters).first()
            return result[0] if result else None