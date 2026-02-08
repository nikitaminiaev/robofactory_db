from typing import Dict
from uuid import UUID
import logging
import hashlib
from repository.bounding_contour_repository import BoundingContourRepository
from repository.module_version_repository import ModuleVersionRepository
from service.brep_storage import save_brep_file
from service.git_manager import init_module_git_repo, commit_module_changes, calculate_brep_files_hash
from models.module_version import ModuleVersion

logger = logging.getLogger(__name__)


def calculate_brep_dict_hash(brep_files_dict: Dict[str, str]) -> str:
    """
    Вычисляет SHA256 хеш содержимого BREP файлов из словаря.

    Args:
        brep_files_dict: Словарь {имя_файла: содержимое}

    Returns:
        SHA256 хеш в виде строки
    """
    if not brep_files_dict:
        return ""

    # Сортируем ключи для консистентности
    sorted_items = sorted(brep_files_dict.items())

    hasher = hashlib.sha256()
    for filename, content in sorted_items:
        hasher.update(content.encode('utf-8'))
        hasher.update(filename.encode('utf-8'))

    return hasher.hexdigest()


class BrepFileService:
    def save_brep_files_from_dict(
        self,
        module_id: UUID,
        brep_files_dict: Dict[str, str],
        description: str = "Update BREP files"
    ) -> ModuleVersion:
        """
        Сохраняет BREP файлы из словаря в файловую систему, обновляет BoundingContour,
        выполняет Git коммит и создает новую версию модуля.

        Args:
            module_id: UUID модуля
            brep_files_dict: Словарь {имя_файла: содержимое_строки}
            description: Описание изменений для коммита и версии

        Returns:
            Созданная ModuleVersion

        Raises:
            OSError: Если не удается сохранить файлы
            CalledProcessError: Если Git команды не удались
            ValueError: Если модуль или bounding_contour не найдены
        """
        if not brep_files_dict:
            raise ValueError("brep_files_dict не может быть пустым")

        version_repo = ModuleVersionRepository()

        # Вычисляем хеш новых файлов
        current_hash = calculate_brep_dict_hash(brep_files_dict)

        # Получаем последнюю версию модуля
        latest_version = version_repo.get_latest_version(module_id)
        if latest_version and latest_version.file_hash == current_hash:
            logger.info(f"Файлы BREP не изменились для модуля {module_id}, пропускаем обновление")
            return latest_version

        saved_paths = {}
        try:
            for filename, content in brep_files_dict.items():
                relative_path = save_brep_file(module_id, filename, content.encode())
                saved_paths[filename] = relative_path
        except OSError as e:
            raise OSError(f"Не удалось сохранить BREP файлы: {e}") from e

        print(f"DEBUG BrepFileService: saved_paths = {saved_paths}")
        contour_repo = BoundingContourRepository()
        contour_repo.update_brep_files(module_id, saved_paths)

        try:
            # Инициализировать git репозиторий если он не существует
            git_repo_path = init_module_git_repo(module_id)
            commit_hash = commit_module_changes(module_id, description)
        except Exception as e:
            raise RuntimeError(f"Не удалось выполнить Git коммит: {e}") from e

        version = version_repo.create_version(
            module_id=module_id,
            version_number="auto",
            description=description,
            commit_hash=commit_hash,
            file_hash=current_hash,
            git_repo_path=git_repo_path
        )

        return version

    def save_single_brep_file(
        self,
        module_id: UUID,
        filename: str,
        file_content: bytes,
        description: str = "Add BREP file"
    ) -> ModuleVersion:
        """
        Сохраняет один BREP файл, обновляет BoundingContour,
        выполняет Git коммит и создает новую версию модуля.

        Args:
            module_id: UUID модуля
            filename: Имя файла
            file_content: Содержимое файла в байтах
            description: Описание изменений для коммита и версии

        Returns:
            Созданная ModuleVersion

        Raises:
            OSError: Если не удается сохранить файл
            CalledProcessError: Если Git команды не удались
            ValueError: Если модуль или bounding_contour не найдены
        """
        # Вычисляем хеш файла
        content_str = file_content.decode('utf-8')
        current_hash = calculate_brep_dict_hash({filename: content_str})

        version_repo = ModuleVersionRepository()
        # Получаем последнюю версию модуля
        latest_version = version_repo.get_latest_version(module_id)
        if latest_version and latest_version.file_hash == current_hash:
            logger.info(f"Файл BREP не изменился для модуля {module_id}, пропускаем обновление")
            return latest_version

        try:
            relative_path = save_brep_file(module_id, filename, file_content)
        except OSError as e:
            raise OSError(f"Не удалось сохранить BREP файл {filename}: {e}") from e

        contour_repo = BoundingContourRepository()
        contour_repo.update_brep_files(module_id, {filename: relative_path})

        try:
            # Инициализировать git репозиторий если он не существует
            git_repo_path = init_module_git_repo(module_id)
            commit_hash = commit_module_changes(module_id, description)
        except Exception as e:
            raise RuntimeError(f"Не удалось выполнить Git коммит: {e}") from e

        version = version_repo.create_version(
            module_id=module_id,
            version_number="auto",
            description=description,
            commit_hash=commit_hash,
            file_hash=current_hash,
            git_repo_path=git_repo_path
        )

        return version
