from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from repository.module_repository import ModuleRepository
from repository.module_version_repository import ModuleVersionRepository
from schemas.module_version_dto import ModuleVersionDTO, ModuleVersionCreateDTO, ModuleVersionUpdateDTO
from service.git_manager import (
    get_module_commit_history,
    checkout_module_commit,
    commit_module_changes,
    init_module_git_repo,
    is_module_git_repo_initialized,
    release_commit_module,
    DirtyWorkingTreeError,
)
from pydantic import BaseModel

router = APIRouter()


@router.get("/modules/{module_id}/versions")
async def get_module_versions(
    module_id: str,
    repo: ModuleVersionRepository = Depends(),
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
    repo: ModuleVersionRepository = Depends(),
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


@router.post("/modules/{module_id}/versions")
async def create_module_version(
    module_id: str,
    body: ModuleVersionCreateDTO,
    version_repo: ModuleVersionRepository = Depends(),
    module_repo: ModuleRepository = Depends(),
):
    try:
        module_uuid = UUID(module_id)

        children_with_coords = module_repo.get_children_coordinates(module_uuid)
        version_metadata = {"children": children_with_coords} if children_with_coords else None

        commit_hash = None
        git_repo_path = None

        if body.make_git_commit or body.is_released:
            if not is_module_git_repo_initialized(module_uuid):
                git_repo_path = init_module_git_repo(module_uuid)
            else:
                existing = version_repo.get_latest_version(module_uuid)
                git_repo_path = existing.git_repo_path if existing else None

            if body.is_released:
                commit_hash = release_commit_module(module_uuid, body.version_number, body.description)
            else:
                commit_hash = commit_module_changes(module_uuid, body.description)

        version = version_repo.create_version(
            module_id=module_uuid,
            version_number=body.version_number,
            description=body.description,
            commit_hash=commit_hash,
            git_repo_path=git_repo_path,
            is_released=body.is_released,
            version_metadata=version_metadata,
        )
        return ModuleVersionDTO.from_module_version(version)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка создания версии: {str(e)}")


@router.patch("/modules/{module_id}/versions/{version_id}/release")
async def release_module_version(
    module_id: str,
    version_id: str,
    repo: ModuleVersionRepository = Depends(),
):
    try:
        version_uuid = UUID(version_id)
        updated_version = repo.update_version_is_released(version_uuid, True)
        return ModuleVersionDTO.from_module_version(updated_version)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка обновления: {str(e)}")


@router.patch("/modules/{module_id}/versions/{version_id}")
async def update_module_version(
    module_id: str,
    version_id: str,
    body: ModuleVersionUpdateDTO,
    repo: ModuleVersionRepository = Depends(),
):
    try:
        version_uuid = UUID(version_id)
        updates = body.model_dump(exclude_none=True)
        updated_version = repo.update_version(version_uuid, **updates)
        return ModuleVersionDTO.from_module_version(updated_version)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка обновления версии: {str(e)}")


@router.get("/modules/{module_id}/commits")
async def get_module_commits(module_id: str):
    try:
        module_uuid = UUID(module_id)
        history = get_module_commit_history(module_uuid)
        return history
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Репозиторий модуля не найден или ошибка: {str(e)}")


class CheckoutRequest(BaseModel):
    commit_hash: str
    force: bool = False


@router.post("/modules/{module_id}/checkout")
async def checkout_module(
    module_id: str,
    request: CheckoutRequest,
):
    try:
        module_uuid = UUID(module_id)
        checkout_module_commit(module_uuid, request.commit_hash, force=request.force)
        return {
            "message": f"Успешно переключено на коммит {request.commit_hash}",
            "commit_hash": request.commit_hash,
        }
    except DirtyWorkingTreeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при checkout: {str(e)}")
