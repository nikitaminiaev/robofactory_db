from pathlib import Path
from uuid import UUID


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
    base_path = Path("resources/brep_files")
    module_path = base_path / str(module_id)
    
    try:
        module_path.mkdir(parents=True, exist_ok=True)
        return str(module_path)
    except OSError as e:
        raise OSError(f"Не удалось создать директорию {module_path}: {e}") from e


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
    base_path = Path("resources/brep_files")
    module_path = base_path / str(module_id)
    
    try:
        module_path.mkdir(parents=True, exist_ok=True)
        file_path = module_path / filename
        file_path.write_bytes(file_content)
        # Относительный путь от api/resources/brep_files/
        relative_path = f"{module_id}/{filename}"
        return relative_path
    except OSError as e:
        raise OSError(f"Не удалось сохранить файл {filename} для модуля {module_id}: {e}") from e