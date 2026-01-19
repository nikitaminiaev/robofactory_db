from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from repository.module_version_repository import ModuleVersionRepository
from schemas.module_version_dto import ModuleVersionDTO

router = APIRouter()

@router.get("/modules/{module_id}/versions")
async def get_module_versions(
    module_id: str,
    repo: ModuleVersionRepository = Depends()
):
    try:
        module_uuid = UUID(module_id)
        versions = repo.get_by_module_id(module_uuid)
        return [ModuleVersionDTO.from_module_version(v) for v in versions]
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Модуль не найден или ошибка: {str(e)}")

@router.get("/modules/{module_id}/versions/latest")
async def get_latest_module_version(
    module_id: str,
    repo: ModuleVersionRepository = Depends()
):
    try:
        module_uuid = UUID(module_id)
        version = repo.get_latest_version(module_uuid)
        if not version:
            raise HTTPException(status_code=404, detail="Версии не найдены")
        return ModuleVersionDTO.from_module_version(version)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Модуль не найден или ошибка: {str(e)}")