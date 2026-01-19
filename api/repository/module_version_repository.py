from typing import Optional, List
from uuid import UUID
from . import BaseRepository
from models import ModuleVersion


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
    
    def create_version(self, module_id: UUID, version_number: str, description: str, commit_hash: Optional[str] = None, git_repo_path: Optional[str] = None, is_released: bool = False) -> ModuleVersion:
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
            git_repo_path=git_repo_path,
            is_released=is_released
        )
        with self.db_session.session() as db:
            db.add(version)
            db.commit()
            db.refresh(version)
        return version