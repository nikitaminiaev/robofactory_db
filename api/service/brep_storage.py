import shutil
from uuid import UUID

from service.constants import build_brep_relative_path, get_module_brep_directory, get_module_resource_path


def create_module_brep_directory(module_id: UUID) -> str:
    """
    Создает директорию для хранения BREP файлов модуля.
    
    Args:
        module_id: UUID модуля
        
    Returns:
        Путь к созданной директории
        
    Raises:
        OSError: Если не удается создать директорию
    """
    module_path_str = f"module {module_id}"
    try:
        module_path = get_module_brep_directory(module_id)
        module_path_str = str(module_path)
        module_path.mkdir(parents=True, exist_ok=True)
        return module_path_str
    except OSError as e:
        raise OSError(f"Не удалось создать директорию {module_path_str}: {e}") from e


def save_brep_file(module_id: UUID, filename: str, file_content: bytes) -> str:
    """
    Сохраняет BREP файл в директорию модуля.
    
    Args:
        module_id: UUID модуля
        filename: Имя файла
        file_content: Содержимое файла
        
    Returns:
        Относительный путь к файлу
        
    Raises:
        OSError: Если не удается создать директорию или записать файл
    """
    module_path = get_module_brep_directory(module_id)
    
    try:
        module_path.mkdir(parents=True, exist_ok=True)
        file_path = module_path / filename
        file_path.write_bytes(file_content)
        return build_brep_relative_path(module_id, filename)
    except OSError as e:
        raise OSError(f"Не удалось сохранить файл {filename} для модуля {module_id}: {e}") from e


def delete_module_brep_directory(module_id: UUID) -> None:
    """
    Удаляет директорию с BREP файлами модуля.

    Args:
        module_id: UUID модуля

    Raises:
        OSError: Если не удается удалить директорию
    """
    module_path = get_module_resource_path(module_id)

    if not module_path.exists():
        return

    if not module_path.is_dir():
        raise OSError(f"Путь {module_path} не является директорией")

    try:
        shutil.rmtree(module_path)
    except OSError as e:
        raise OSError(f"Не удалось удалить директорию {module_path}: {e}") from e