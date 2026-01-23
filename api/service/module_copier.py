from uuid import UUID
from repository.module_repository import ModuleRepository
from repository.module_version_repository import ModuleVersionRepository
from models import Module

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
    module_repo = ModuleRepository()
    new_module = module_repo.copy_module_with_roles(
        module_id=module_id,
        new_author=new_author,
        version_number=version_number,
        description=description
    )
    # Создать запись ModuleVersion с Git интеграцией
    version_repo = ModuleVersionRepository()
    version = version_repo.create_version_with_git(
        module_id=new_module.id,
        version_number=version_number,
        description=description
    )
    return new_module