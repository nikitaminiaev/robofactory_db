import uuid as uuid_mod
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import selectinload
from sqlalchemy import func, select

from . import BaseRepository
from .bounding_contour_repository import BoundingContourRepository
from models import Module, ModuleBoundary, ModuleRole
from models.associations import (
    parent_child_module,
    parent_child_module_role_assignment,
    module_stream,
    module_platform,
    module_boundary,
)
from service.brep_storage import delete_module_brep_directory


class ModuleRepository(BaseRepository):
    def get_modules_with_relations(self, limit: int = 10, offset: int = 0) -> list[Module]:
        with (self.db_session.session() as db):
            query = db.query(Module).options(
                selectinload(Module.bounding_contour),
                selectinload(Module.children),
                selectinload(Module.parents),
                selectinload(Module.boundaries),
                selectinload(Module.streams),
                selectinload(Module.platforms),
                selectinload(Module.versions),
                selectinload(Module.roles),
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
                selectinload(Module.platforms),
                selectinload(Module.versions),
                selectinload(Module.roles),
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
                selectinload(Module.platforms),
                selectinload(Module.versions),
                selectinload(Module.roles),
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
                selectinload(Module.platforms),
                selectinload(Module.versions),
                selectinload(Module.roles),
            ).filter_by(id=id).first()
            print(f"DEBUG get_module_with_relations_by_id: module found = {module is not None}")
            if module:
                print(f"DEBUG get_module_with_relations_by_id: module.id = {module.id}")
                print(f"DEBUG get_module_with_relations_by_id: bounding_contour = {module.bounding_contour is not None}")
                if module.bounding_contour:
                    print(f"DEBUG get_module_with_relations_by_id: contour.brep_files = {module.bounding_contour.brep_files}")
        return module

    def get_child_counts(self, parent_id: UUID) -> dict:
        """
        Возвращает словарь {child_id_str: количество_вхождений} для родителя.
        Считает строки в parent_child_module через GROUP BY.
        """
        with self.db_session.session() as db:
            stmt = (
                select(
                    parent_child_module.c.child_id,
                    func.count().label('cnt'),
                )
                .where(parent_child_module.c.parent_id == parent_id)
                .group_by(parent_child_module.c.child_id)
            )
            rows = db.execute(stmt).fetchall()
            return {str(row.child_id): row.cnt for row in rows}

    def get_parent_counts(self, child_id: UUID) -> dict:
        """
        Возвращает словарь {parent_id_str: количество_вхождений} для ребёнка.
        Считает строки в parent_child_module через GROUP BY.
        """
        with self.db_session.session() as db:
            stmt = (
                select(
                    parent_child_module.c.parent_id,
                    func.count().label('cnt'),
                )
                .where(parent_child_module.c.child_id == child_id)
                .group_by(parent_child_module.c.parent_id)
            )
            rows = db.execute(stmt).fetchall()
            return {str(row.parent_id): row.cnt for row in rows}

    def get_children_roles(self, parent_id: UUID) -> dict:
        """
        Возвращает словарь {child_id_str: [role_id_str, ...]} — роли, назначенные
        каждому дочернему модулю (для отображения состояния чекбоксов в матрице).
        """
        from models.associations import module_role_assignment
        with self.db_session.session() as db:
            children_ids = db.execute(
                select(parent_child_module.c.child_id).where(
                    parent_child_module.c.parent_id == parent_id
                ).distinct()
            ).scalars().all()

            if not children_ids:
                return {}

            rows = db.execute(
                select(
                    module_role_assignment.c.module_id,
                    module_role_assignment.c.role_id,
                ).where(module_role_assignment.c.module_id.in_(children_ids))
            ).fetchall()

        result: dict = {}
        for row in rows:
            key = str(row.module_id)
            result.setdefault(key, []).append(str(row.role_id))
        return result

    def get_children_coordinates(self, parent_id: UUID) -> List[dict]:
        """
        Возвращает список всех записей children для данного родителя, включая дубликаты.
        Каждая запись содержит parent_child_module_id, child_id и coordinates.
        Используется при загрузке сборки для создания нескольких копий одного объекта.
        
        Returns:
            List[dict]: [{"parent_child_module_id": "uuid", "child_id": "uuid", "coordinates": {...}, "role_id": "uuid|None", "role_ids": [...]}, ...]
        """
        with self.db_session.session() as db:
            stmt = (
                select(
                    parent_child_module.c.id,
                    parent_child_module.c.child_id,
                    parent_child_module.c.coordinates,
                    parent_child_module.c.role_id,
                )
                .where(parent_child_module.c.parent_id == parent_id)
            )
            rows = db.execute(stmt).fetchall()
            link_ids = [row.id for row in rows]
            role_rows = []
            if link_ids:
                role_rows = db.execute(
                    select(
                        parent_child_module_role_assignment.c.parent_child_module_id,
                        parent_child_module_role_assignment.c.role_id,
                    ).where(parent_child_module_role_assignment.c.parent_child_module_id.in_(link_ids))
                ).fetchall()

            role_map: dict[str, list[str]] = {}
            for role_row in role_rows:
                link_id = str(role_row.parent_child_module_id)
                role_map.setdefault(link_id, []).append(str(role_row.role_id))

            return [
                {
                    "parent_child_module_id": str(row.id),
                    "child_id": str(row.child_id),
                    "coordinates": row.coordinates,
                    "role_id": str(row.role_id) if row.role_id else None,
                    "role_ids": role_map.get(str(row.id), [str(row.role_id)] if row.role_id else []),
                }
                for row in rows
            ]

    def get_parent_edges_with_roles(self, child_id: UUID) -> List[dict]:
        """
        Возвращает список связей parent_child_module для текущего child,
        включая роль связи (если задана).
        """
        with self.db_session.session() as db:
            stmt = (
                select(
                    parent_child_module.c.id,
                    parent_child_module.c.parent_id,
                    parent_child_module.c.role_id,
                    ModuleRole.name,
                    ModuleRole.description,
                )
                .outerjoin(ModuleRole, ModuleRole.id == parent_child_module.c.role_id)
                .where(parent_child_module.c.child_id == child_id)
                .order_by(parent_child_module.c.parent_id, parent_child_module.c.id)
            )
            rows = db.execute(stmt).fetchall()

        result = []
        for row in rows:
            result.append(
                {
                    "parent_child_module_id": str(row.id),
                    "parent_id": str(row.parent_id),
                    "role_id": str(row.role_id) if row.role_id else None,
                    "role_name": row.name,
                    "role_description": row.description,
                }
            )
        return result

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
                selectinload(Module.platforms),
                selectinload(Module.versions),
                selectinload(Module.roles),
            )
            
            query = query.join(
                parent_child_module,
                Module.id == parent_child_module.c.child_id
            ).filter(parent_child_module.c.parent_id == parent_id).distinct()

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
                selectinload(Module.platforms),
                selectinload(Module.versions),
                selectinload(Module.roles),
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

    def remove_child_relations(self, parent_id: UUID, relation_ids: List[UUID], db_session):
        """
        Удаляет конкретные связи по parent_child_module_id
        """
        if not relation_ids:
            return
        db_session.execute(
            parent_child_module.delete().where(
                (parent_child_module.c.parent_id == parent_id) &
                (parent_child_module.c.id.in_(relation_ids))
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
        Добавляет связь с дочерним модулем.
        Каждый вызов создаёт новую строку с уникальным id — позволяет иметь
        несколько вхождений одного дочернего модуля с разными координатами.
        """
        target_db = db_session if db_session else self.db_session.session()
        relation_id = uuid_mod.uuid4()
        target_db.execute(
            parent_child_module.insert().values(
                id=relation_id,
                parent_id=parent_id,
                child_id=child_id,
                coordinates=coordinates,
                role_id=role_id,
            )
        )
        if role_id:
            target_db.execute(
                parent_child_module_role_assignment.insert().values(
                    parent_child_module_id=relation_id,
                    role_id=role_id,
                )
            )

    def add_parent_relation(self, child_id: UUID, parent_id: UUID, coordinates: Optional[dict] = None, role_id: Optional[UUID] = None, db_session = None):
        """
        Добавляет связь с родительским модулем.
        Каждый вызов создаёт новую строку с уникальным id.
        """
        target_db = db_session if db_session else self.db_session.session()
        relation_id = uuid_mod.uuid4()
        target_db.execute(
            parent_child_module.insert().values(
                id=relation_id,
                parent_id=parent_id,
                child_id=child_id,
                coordinates=coordinates,
                role_id=role_id,
            )
        )
        if role_id:
            target_db.execute(
                parent_child_module_role_assignment.insert().values(
                    parent_child_module_id=relation_id,
                    role_id=role_id,
                )
            )

    def copy_module_with_roles(self, module_id: UUID, new_author: str, version_number: str, description: str) -> Module:
        """
        Копирует модуль с указанными параметрами, копируя все его роли и bounding_contour.

        Args:
            module_id: UUID оригинального модуля
            new_author: Автор копии
            version_number: Номер версии для копии
            description: Описание версии

        Returns:
            Новый модуль

        Raises:
            ValueError: Если модуль не найден
        """
        with self.db_session.session() as db:
            # Получить оригинальный модуль с отношениями
            original = db.query(Module).options(
                selectinload(Module.bounding_contour),
            ).filter_by(id=module_id).first()

            if not original:
                raise ValueError("Module not found")

            # Создать копию модуля
            new_module = Module(
                name=original.name,
                abbreviation=original.abbreviation,
                author=new_author,
                description=description,
                ttx=original.ttx,
                implementation=original.implementation,
                status=original.status,
                is_lts=original.is_lts,
                service_id=original.service_id,
                interface_object_id=original.interface_object_id
            )

            db.add(new_module)
            db.flush()  # Получить id для нового модуля

            # Копировать bounding_contour в той же транзакции, чтобы FK-constraint
            # не упал: новый модуль ещё не закоммичен в этой точке.
            if original.bounding_contour:
                bounding_contour_repo = BoundingContourRepository()
                bounding_contour_repo.copy_bounding_contour(original.id, new_module.id, db_session=db)

            # Копировать роли из parent_child_module
            # Где оригинальный модуль - child
            child_relations = db.query(parent_child_module).filter(
                parent_child_module.c.child_id == module_id
            ).all()
            for rel in child_relations:
                new_relation_id = uuid_mod.uuid4()
                db.execute(parent_child_module.insert().values(
                    id=new_relation_id,
                    parent_id=rel.parent_id,
                    child_id=new_module.id,
                    coordinates=rel.coordinates,
                    role_id=rel.role_id,
                ))
                role_rows = db.execute(
                    select(parent_child_module_role_assignment.c.role_id).where(
                        parent_child_module_role_assignment.c.parent_child_module_id == rel.id
                    )
                ).fetchall()
                for role_row in role_rows:
                    db.execute(
                        parent_child_module_role_assignment.insert().values(
                            parent_child_module_id=new_relation_id,
                            role_id=role_row.role_id,
                        )
                    )

            # Где оригинальный модуль - parent
            parent_relations = db.query(parent_child_module).filter(
                parent_child_module.c.parent_id == module_id
            ).all()
            for rel in parent_relations:
                new_relation_id = uuid_mod.uuid4()
                db.execute(parent_child_module.insert().values(
                    id=new_relation_id,
                    parent_id=new_module.id,
                    child_id=rel.child_id,
                    coordinates=rel.coordinates,
                    role_id=rel.role_id,
                ))
                role_rows = db.execute(
                    select(parent_child_module_role_assignment.c.role_id).where(
                        parent_child_module_role_assignment.c.parent_child_module_id == rel.id
                    )
                ).fetchall()
                for role_row in role_rows:
                    db.execute(
                        parent_child_module_role_assignment.insert().values(
                            parent_child_module_id=new_relation_id,
                            role_id=role_row.role_id,
                        )
                    )

            db.commit()

            # Получить обновленный объект с отношениями
            new_module = db.query(Module).options(
                selectinload(Module.bounding_contour),
                selectinload(Module.children),
                selectinload(Module.parents),
                selectinload(Module.streams),
                selectinload(Module.platforms),
                selectinload(Module.boundaries),
                selectinload(Module.versions),
                selectinload(Module.roles),
            ).filter_by(id=new_module.id).first()

            return new_module

    def delete_module(self, module_id: UUID) -> None:
        """
        Удаляет модуль и все связанные сущности, кроме родительских и дочерних модулей.
        Удаляет ассоциации с иерархией, но сохраняет сами модули.

        Args:
            module_id: UUID модуля для удаления

        Raises:
            ValueError: Если модуль не найден
        """
        with self.db_session.session() as db:
            # Получить модуль для проверки существования
            module = db.query(Module).filter_by(id=module_id).first()
            if not module:
                raise ValueError(f"Модуль с id {module_id} не найден")

            # Удалить связанные сущности
            # Удалить bounding_contour
            if module.bounding_contour:
                db.delete(module.bounding_contour)

            # Удалить ModuleBoundary сущности
            db.query(ModuleBoundary).filter(
                ModuleBoundary.id.in_(
                    db.query(module_boundary.c.boundary_id).filter(
                        module_boundary.c.module_id == module_id
                    )
                )
            ).delete(synchronize_session=False)

            # Удалить ассоциации с streams
            db.execute(
                module_stream.delete().where(module_stream.c.module_id == module_id)
            )

            # Удалить ассоциации с platforms
            db.execute(
                module_platform.delete().where(module_platform.c.module_id == module_id)
            )

            # Удалить ассоциации с boundaries (уже удалены сущности, но на всякий случай)
            db.execute(
                module_boundary.delete().where(module_boundary.c.module_id == module_id)
            )

            # Удалить ассоциации parent-child, но сохранить модули
            # Где модуль - parent
            db.execute(
                parent_child_module.delete().where(parent_child_module.c.parent_id == module_id)
            )
            # Где модуль - child
            db.execute(
                parent_child_module.delete().where(parent_child_module.c.child_id == module_id)
            )

            # Удалить файлы BREP модуля из файловой системы
            delete_module_brep_directory(module_id)

            # Удалить модуль (versions удалятся автоматически из-за cascade)
            db.delete(module)

            db.commit()