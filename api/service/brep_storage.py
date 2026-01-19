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
    base_path = Path("api/resources/brep_files")
    module_path = base_path / str(module_id)
    
    try:
        module_path.mkdir(parents=True, exist_ok=True)
        return str(module_path)
    except OSError as e:
        raise OSError(f"Не удалось создать директорию {module_path}: {e}") from e