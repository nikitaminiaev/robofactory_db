from typing import Dict
from uuid import UUID
import hashlib
from service.constants import get_module_resource_path
from repository.bounding_contour_repository import BoundingContourRepository
from repository.module_version_repository import ModuleVersionRepository
from service.brep_storage import save_brep_file
from service.git_manager import commit_module_changes, init_module_git_repo, is_module_git_repo_initialized
from models.module_version import ModuleVersion


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
    @staticmethod
    def _create_initial_version_if_needed(
        module_id: UUID,
        description: str,
        file_hash: str,
    ) -> ModuleVersion:
        version_repo = ModuleVersionRepository()
        latest_version = version_repo.get_latest_version(module_id)
        if latest_version:
            return latest_version

        git_repo_path = str(get_module_resource_path(module_id))
        if not is_module_git_repo_initialized(module_id):
            git_repo_path = init_module_git_repo(module_id)
        commit_hash = commit_module_changes(module_id, description)
        return version_repo.create_version(
            module_id=module_id,
            version_number="auto",
            description=description,
            commit_hash=commit_hash,
            file_hash=file_hash,
            git_repo_path=git_repo_path,
        )

    def save_brep_files_from_dict(
        self,
        module_id: UUID,
        brep_files_dict: Dict[str, str],
        description: str = "Update BREP files"
    ) -> ModuleVersion:
        """
        Сохраняет BREP файлы из словаря и обновляет BoundingContour.
        Инициализирующий Git-коммит и версия создаются только один раз.

        Args:
            module_id: UUID модуля
            brep_files_dict: Словарь {имя_файла: содержимое_строки}
            description: Описание изменений для коммита и версии

        Returns:
            Созданная ModuleVersion

        Raises:
            OSError: Если не удается сохранить файлы
            RuntimeError: Если не удалось создать инициализирующую версию
        """
        if not brep_files_dict:
            raise ValueError("brep_files_dict не может быть пустым")

        current_hash = calculate_brep_dict_hash(brep_files_dict)

        saved_paths = {}
        try:
            for filename, content in brep_files_dict.items():
                relative_path = save_brep_file(module_id, filename, content.encode())
                saved_paths[filename] = relative_path
        except OSError as e:
            raise OSError(f"Не удалось сохранить BREP файлы: {e}") from e

        contour_repo = BoundingContourRepository()
        contour_repo.update_brep_files(module_id, saved_paths)

        try:
            return self._create_initial_version_if_needed(
                module_id=module_id,
                description=description,
                file_hash=current_hash,
            )
        except Exception as e:
            raise RuntimeError(f"Не удалось создать инициализирующую версию: {e}") from e

    def save_single_brep_file(
        self,
        module_id: UUID,
        filename: str,
        file_content: bytes,
        description: str = "Add BREP file"
    ) -> ModuleVersion:
        """
        Сохраняет один BREP файл и обновляет BoundingContour.

        Args:
            module_id: UUID модуля
            filename: Имя файла
            file_content: Содержимое файла в байтах
            description: Описание изменений для коммита и версии

        Returns:
            Созданная ModuleVersion

        Raises:
            OSError: Если не удается сохранить файл
            RuntimeError: Если не удалось создать инициализирующую версию
        """
        content_str = file_content.decode("utf-8")

        try:
            relative_path = save_brep_file(module_id, filename, file_content)
        except OSError as e:
            raise OSError(f"Не удалось сохранить BREP файл {filename}: {e}") from e

        contour_repo = BoundingContourRepository()
        contour_repo.update_brep_files(module_id, {filename: relative_path})

        try:
            return self._create_initial_version_if_needed(
                module_id=module_id,
                description=description,
                file_hash=calculate_brep_dict_hash({filename: content_str}),
            )
        except Exception as e:
            raise RuntimeError(f"Не удалось создать инициализирующую версию: {e}") from e
