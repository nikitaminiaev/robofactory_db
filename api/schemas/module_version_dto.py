from typing import Optional, Any, Dict
from pydantic import BaseModel


class ModuleVersionDTO(BaseModel):
    id: str
    module_id: str
    version_number: str
    commit_hash: Optional[str] = None
    description: str
    git_repo_path: Optional[str] = None
    is_released: bool
    created_ts: Optional[str] = None
    version_metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_module_version(cls, version):
        return cls(
            id=str(version.id),
            module_id=str(version.module_id),
            version_number=version.version_number,
            commit_hash=version.commit_hash,
            description=version.description,
            git_repo_path=version.git_repo_path,
            is_released=version.is_released,
            created_ts=version.created_ts.isoformat() if version.created_ts else None,
            version_metadata=version.version_metadata,
        )

    class Config:
        from_attributes = True


class ModuleVersionCreateDTO(BaseModel):
    version_number: str
    description: str
    is_released: bool = False
    make_git_commit: bool = False


class ModuleVersionUpdateDTO(BaseModel):
    version_number: Optional[str] = None
    description: Optional[str] = None
    is_released: Optional[bool] = None
