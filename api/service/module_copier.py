from typing import Optional
from uuid import UUID
from sqlalchemy.orm import selectinload
from repository.db_session import Db_session
from repository.module_version_repository import ModuleVersionRepository
from models import Module, ModuleVersion, BoundingContour
from models.associations import parent_child_module


def copy_module_with_roles(module_id: UUID, new_author: str, version_number: str, description: str) -> Module:
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
    db_session_factory = Db_session().session
    
    with db_session_factory() as db:
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
        
        # Копировать bounding_contour если есть
        if original.bounding_contour:
            new_contour = BoundingContour(
                module_id=new_module.id,
                is_assembly=original.bounding_contour.is_assembly,
                is_shell=original.bounding_contour.is_shell,
                brep_files=original.bounding_contour.brep_files,
                parent_id=None  # Для копии не копируем hierarchy
            )
            db.add(new_contour)
        
        # Копировать роли из parent_child_module
        # Где оригинальный модуль - child
        child_relations = db.query(parent_child_module).filter(
            parent_child_module.c.child_id == module_id
        ).all()
        for rel in child_relations:
            db.execute(parent_child_module.insert().values(
                parent_id=rel.parent_id,
                child_id=new_module.id,
                coordinates=rel.coordinates,
                role_id=rel.role_id
            ))
        
        # Где оригинальный модуль - parent
        parent_relations = db.query(parent_child_module).filter(
            parent_child_module.c.parent_id == module_id
        ).all()
        for rel in parent_relations:
            db.execute(parent_child_module.insert().values(
                parent_id=new_module.id,
                child_id=rel.child_id,
                coordinates=rel.coordinates,
                role_id=rel.role_id
            ))
        
        # Создать запись ModuleVersion с Git интеграцией
        from service.git_manager import init_module_git_repo, commit_module_changes

        # Проверить, есть ли уже git_repo_path для модуля
        existing_version = db.query(ModuleVersion).filter_by(module_id=new_module.id).first()
        git_repo_path = existing_version.git_repo_path if existing_version else None

        if not git_repo_path:
            # Инициализировать репозиторий
            git_repo_path = init_module_git_repo(new_module.id)

        # Коммит изменений
        commit_hash = commit_module_changes(new_module.id, description)

        # Создать версию в той же сессии
        version = ModuleVersion(
            module_id=new_module.id,
            version_number=version_number,
            description=description,
            commit_hash=commit_hash,
            git_repo_path=git_repo_path
        )
        db.add(version)

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
        ).filter_by(id=new_module.id).first()

        return new_module