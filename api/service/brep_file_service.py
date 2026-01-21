from typing import Dict
from uuid import UUID
from models import Module
from repository.module_version_repository import ModuleVersionRepository
from service.brep_storage import save_brep_file
from service.git_manager import commit_module_changes
from sqlalchemy.orm import selectinload
from repository.db_session import Db_session
from models.module_version import ModuleVersion


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
        
        # Сохранить файлы и собрать пути
        saved_paths = {}
        try:
            for filename, content in brep_files_dict.items():
                relative_path = save_brep_file(module_id, filename, content.encode())
                saved_paths[filename] = relative_path
        except OSError as e:
            raise OSError(f"Не удалось сохранить BREP файлы: {e}") from e
        
        # Обновить bounding_contour
        db_session_factory = Db_session().session
        with db_session_factory() as db:
            module = db.query(Module).options(selectinload(Module.bounding_contour)).filter_by(id=module_id).first()
            if not module:
                raise ValueError(f"Модуль с id {module_id} не найден")
            if not module.bounding_contour:
                raise ValueError(f"BoundingContour для модуля {module_id} не найден")
            
            if module.bounding_contour.brep_files is None:
                module.bounding_contour.brep_files = {}
            module.bounding_contour.brep_files.update(saved_paths)
            db.commit()
        
        # Git коммит
        try:
            commit_hash = commit_module_changes(module_id, description)
        except Exception as e:
            raise RuntimeError(f"Не удалось выполнить Git коммит: {e}") from e
        
        # Создать версию
        repo = ModuleVersionRepository()
        version = repo.create_version(
            module_id=module_id,
            version_number="auto",
            description=description,
            commit_hash=commit_hash
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
        # Сохранить файл
        try:
            relative_path = save_brep_file(module_id, filename, file_content)
        except OSError as e:
            raise OSError(f"Не удалось сохранить BREP файл {filename}: {e}") from e
        
        # Обновить bounding_contour
        db_session_factory = Db_session().session
        with db_session_factory() as db:
            module = db.query(Module).options(selectinload(Module.bounding_contour)).filter_by(id=module_id).first()
            if not module:
                raise ValueError(f"Модуль с id {module_id} не найден")
            if not module.bounding_contour:
                raise ValueError(f"BoundingContour для модуля {module_id} не найден")
            
            if module.bounding_contour.brep_files is None:
                module.bounding_contour.brep_files = {}
            module.bounding_contour.brep_files[filename] = relative_path
            db.commit()
        
        # Git коммит
        try:
            commit_hash = commit_module_changes(module_id, description)
        except Exception as e:
            raise RuntimeError(f"Не удалось выполнить Git коммит: {e}") from e
        
        # Создать версию
        repo = ModuleVersionRepository()
        version = repo.create_version(
            module_id=module_id,
            version_number="auto",
            description=description,
            commit_hash=commit_hash
        )
        
        return version