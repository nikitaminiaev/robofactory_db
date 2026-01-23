from typing import Optional, List
from uuid import UUID
from . import BaseRepository
from models import ModuleVersion
from service.git_manager import init_module_git_repo, commit_module_changes


class ModuleVersionRepository(BaseRepository):
    def get_by_module_id(self, module_id: UUID) -> List[ModuleVersion]:
        """
        Получить все версии модуля по module_id.
        
        Args:
            module_id: UUID модуля
            
        Returns:
            Список ModuleVersion
        """
        with self.db_session.session() as db:
            versions = db.query(ModuleVersion).filter_by(module_id=module_id).order_by(ModuleVersion.created_ts).all()
        return versions
    
    def get_latest_version(self, module_id: UUID) -> Optional[ModuleVersion]:
        """
        Получить последнюю версию модуля по module_id.
        
        Args:
            module_id: UUID модуля
            
        Returns:
            Последняя ModuleVersion или None
        """
        with self.db_session.session() as db:
            version = db.query(ModuleVersion).filter_by(module_id=module_id).order_by(ModuleVersion.created_ts.desc()).first()
        return version
    
    def create_version(self, module_id: UUID, version_number: str, description: str, commit_hash: Optional[str] = None, file_hash: Optional[str] = None, git_repo_path: Optional[str] = None, is_released: bool = False) -> ModuleVersion:
        """
        Создать новую версию модуля.
        
        Args:
            module_id: UUID модуля
            version_number: Номер версии
            description: Описание
            commit_hash: Хеш коммита (опционально)
            git_repo_path: Путь к git репозиторию (опционально)
            is_released: Флаг релиза
            
        Returns:
            Созданная ModuleVersion
        """
        version = ModuleVersion(
            module_id=module_id,
            version_number=version_number,
            description=description,
            commit_hash=commit_hash,
            file_hash=file_hash,
            git_repo_path=git_repo_path,
            is_released=is_released
        )
        with self.db_session.session() as db:
            db.add(version)
            db.commit()
            db.refresh(version)
        return version
    
    def update_version_is_released(self, version_id: UUID, is_released: bool) -> ModuleVersion:
        """
        Обновить флаг is_released для версии.
        
        Args:
            version_id: UUID версии
            is_released: Новое значение
            
        Returns:
            Обновленная ModuleVersion
            
        Raises:
            ValueError: Если версия не найдена
        """
        with self.db_session.session() as db:
            version = db.query(ModuleVersion).filter_by(id=version_id).first()
            if not version:
                raise ValueError("Version not found")
            version.is_released = is_released
            db.commit()
            db.refresh(version)
        return version
    
    def create_version_with_git(self, module_id: UUID, version_number: str, description: str) -> ModuleVersion:
        """
        Создать версию с Git интеграцией.
        
        Args:
            module_id: UUID модуля
            version_number: Номер версии
            description: Описание
            
        Returns:
            Созданная ModuleVersion
        """
        # Проверить, есть ли уже git_repo_path для модуля
        with self.db_session.session() as db:
            existing_version = db.query(ModuleVersion).filter_by(module_id=module_id).first()
            git_repo_path = existing_version.git_repo_path if existing_version else None
            
            if not git_repo_path:
                # Инициализировать репозиторий
                git_repo_path = init_module_git_repo(module_id)
            
            # Коммит изменений
            commit_hash = commit_module_changes(module_id, description)
            
            # Создать версию
            version = ModuleVersion(
                module_id=module_id,
                version_number=version_number,
                description=description,
                commit_hash=commit_hash,
                git_repo_path=git_repo_path
            )
            db.add(version)
            db.commit()
            db.refresh(version)
        return version