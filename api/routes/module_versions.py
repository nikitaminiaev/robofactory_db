from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from repository.module_version_repository import ModuleVersionRepository
from schemas.module_version_dto import ModuleVersionDTO
from service.git_manager import get_module_commit_history, checkout_module_commit
from pydantic import BaseModel

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

@router.patch("/modules/{module_id}/versions/{version_id}/release")
async def release_module_version(
    module_id: str,
    version_id: str,
    repo: ModuleVersionRepository = Depends()
):
    try:
        version_uuid = UUID(version_id)
        updated_version = repo.update_version_is_released(version_uuid, True)
        return ModuleVersionDTO.from_module_version(updated_version)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка обновления: {str(e)}")

@router.get("/modules/{module_id}/commits")
async def get_module_commits(
    module_id: str
):
    try:
        module_uuid = UUID(module_id)
        history = get_module_commit_history(module_uuid)
        return history
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Репозиторий модуля не найден или ошибка: {str(e)}")


class CheckoutRequest(BaseModel):
    commit_hash: str


@router.post("/modules/{module_id}/checkout")
async def checkout_module(
    module_id: str,
    request: CheckoutRequest
):
    """
    Выполняет git checkout на указанный коммит для модуля.
    
    Args:
        module_id: UUID модуля
        request: Объект с commit_hash для checkout
        
    Returns:
        Сообщение об успешном checkout
    """
    try:
        module_uuid = UUID(module_id)
        checkout_module_commit(module_uuid, request.commit_hash)
        return {
            "message": f"Успешно переключено на коммит {request.commit_hash}",
            "commit_hash": request.commit_hash
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при checkout: {str(e)}")