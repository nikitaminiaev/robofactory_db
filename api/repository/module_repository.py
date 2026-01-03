from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from . import BaseRepository
from models import Module
from models.associations import parent_child_module


class ModuleRepository(BaseRepository):
    def get_modules_with_relations(self, limit: int = 10, offset: int = 0) -> list[Module]:
        with (self.db_session.session() as db):
            query = db.query(Module).options(
                selectinload(Module.bounding_contour),
                selectinload(Module.children),
                selectinload(Module.parents),
                selectinload(Module.boundaries),
                selectinload(Module.streams),
                selectinload(Module.platforms)
            ).order_by(
                Module.id
            )
            
            query = query.offset(offset)
            query = query.limit(limit)
                
            modules = query.all()
        return modules
    
    def get_top_level_modules_with_relations(self, limit: int = 10, offset: int = 0, top_level_ids: Optional[list[UUID]] = None) -> list[Module]:
        with (self.db_session.session() as db):
            query = db.query(Module).options(
                selectinload(Module.bounding_contour),
                selectinload(Module.children),
                selectinload(Module.parents),
                selectinload(Module.boundaries),
                selectinload(Module.streams),
                selectinload(Module.platforms)
            )
            
            if top_level_ids is None:
                query = query.filter(~Module.parents.any())
            else:
                query = query.filter(Module.parents.any(Module.id.in_(top_level_ids)))
                
            query = query.order_by(Module.id)
            query = query.offset(offset)
            query = query.limit(limit)
                
            modules = query.all()
        return modules

    def get_count_of_modules(self) -> int:
        with (self.db_session.session() as db):
            count = db.query(Module).count()
        return count

    def get_module(self, name: str) -> Module:
        with self.db_session.session() as db:
            module = db.query(Module).filter_by(name=name).first()
        return module

    def get_module_with_relations(self, name: Optional[str] = None, author: Optional[str] = None, created_ts: Optional[str] = None) -> list[Module]:
        with self.db_session.session() as db:
            query = db.query(Module).options(
                selectinload(Module.bounding_contour),
                selectinload(Module.children),
                selectinload(Module.parents),
                selectinload(Module.boundaries),
                selectinload(Module.streams),
                selectinload(Module.platforms)
            )
            
            if name:
                query = query.filter(Module.name.ilike(f"%{name}%"))
            if author:
                query = query.filter(Module.author.ilike(f"%{author}%"))
            if created_ts:
                # Поиск объектов, созданных после указанной даты
                query = query.filter(func.date(Module.created_ts) > created_ts)
                
            return query.all()
    
    def get_module_by_id(self, id: UUID) -> Module:
        with self.db_session.session() as db:
            module = db.query(Module).filter_by(id=id).first()
        return module

    def get_module_for_update(self, id: UUID, db_session) -> Module:
        return db_session.query(Module).filter_by(id=id).first()

    def get_module_with_relations_by_id(self, id: UUID) -> Module:
        with self.db_session.session() as db:
            module = db.query(Module).options(
                selectinload(Module.bounding_contour),
                selectinload(Module.children),
                selectinload(Module.parents),
                selectinload(Module.boundaries),
                selectinload(Module.streams),
                selectinload(Module.platforms)
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

    def get_children_modules_with_relations(self, parent_id: UUID) -> list[Module]:
        with (self.db_session.session() as db):
            query = db.query(Module).options(
                selectinload(Module.bounding_contour),
                selectinload(Module.children),
                selectinload(Module.parents),
                selectinload(Module.boundaries),
                selectinload(Module.streams),
                selectinload(Module.platforms)
            )
            
            query = query.join(
                parent_child_module,
                Module.id == parent_child_module.c.child_id
            ).filter(parent_child_module.c.parent_id == parent_id)
            
            query = query.order_by(Module.id)
            
            modules = query.all()
        return modules

    def get_parents_modules_with_relations(self, child_id: UUID) -> list[Module]:
        with (self.db_session.session() as db):
            query = db.query(Module).options(
                selectinload(Module.bounding_contour),
                selectinload(Module.children),
                selectinload(Module.parents),
                selectinload(Module.boundaries),
                selectinload(Module.streams),
                selectinload(Module.platforms)
            )
            
            query = query.join(
                parent_child_module,
                Module.id == parent_child_module.c.parent_id
            ).filter(parent_child_module.c.child_id == child_id)
            
            query = query.order_by(Module.id)
            
            modules = query.all()
        return modules

    def get_modules_names_by_ids(self, ids: list[UUID]) -> dict[str, str]:
        """
        Получает словарь с именами модулей по их идентификаторам
        
        Args:
            ids: список UUID идентификаторов модулей
            
        Returns:
            словарь, где ключ - строковое представление UUID, а значение - имя модуля
        """
        if not ids:
            return {}
            
        with self.db_session.session() as db:
            query = db.query(Module.id, Module.name).filter(Module.id.in_(ids))
            results = query.all()
            return {str(id): name for id, name in results}

    def remove_children(self, parent_id: UUID, child_ids: List[UUID], db_session):
        """
        Удаляет связи с дочерними модулями
        """
        if not child_ids:
            return
        db_session.execute(
            parent_child_module.delete().where(
                (parent_child_module.c.parent_id == parent_id) &
                (parent_child_module.c.child_id.in_(child_ids))
            )
        )

    def remove_parents(self, child_id: UUID, parent_ids: List[UUID], db_session):
        """
        Удаляет связи с родительскими модулями
        """
        if not parent_ids:
            return
        db_session.execute(
            parent_child_module.delete().where(
                (parent_child_module.c.child_id == child_id) &
                (parent_child_module.c.parent_id.in_(parent_ids))
            )
        )

    def add_child_relation(self, parent_id: UUID, child_id: UUID, coordinates: Optional[dict] = None, role_id: Optional[UUID] = None, db_session = None):
        """
        Добавляет связь с дочерним модулем
        """
        target_db = db_session if db_session else self.db_session.session()
        target_db.execute(
            parent_child_module.insert().values(
                parent_id=parent_id,
                child_id=child_id,
                coordinates=coordinates,
                role_id=role_id
            )
        )

    def add_parent_relation(self, child_id: UUID, parent_id: UUID, coordinates: Optional[dict] = None, role_id: Optional[UUID] = None, db_session = None):
        """
        Добавляет связь с родительским модулем
        """
        target_db = db_session if db_session else self.db_session.session()
        target_db.execute(
            parent_child_module.insert().values(
                parent_id=parent_id,
                child_id=child_id,
                coordinates=coordinates,
                role_id=role_id
            )
        )