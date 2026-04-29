from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from repository.role_repository import RoleRepository
from repository.module_repository import ModuleRepository

router = APIRouter()


class RoleAssignRequest(BaseModel):
    role_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None


class RoleUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class RoleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None


@router.get("/modules/{module_id}/roles")
async def get_module_roles(
    module_id: str,
    role_repo: RoleRepository = Depends(),
    module_repo: ModuleRepository = Depends(),
):
    try:
        module_uuid = UUID(module_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат module_id")

    module = module_repo.get_module_by_id(module_uuid)
    if not module:
        raise HTTPException(status_code=404, detail=f"Модуль с ID '{module_id}' не найден")

    roles = role_repo.fetch_module_roles(module_uuid)
    return [RoleResponse(id=str(r.id), name=r.name, description=r.description) for r in roles]


@router.post("/modules/{module_id}/roles", status_code=201)
async def add_role_to_module(
    module_id: str,
    body: RoleAssignRequest,
    role_repo: RoleRepository = Depends(),
    module_repo: ModuleRepository = Depends(),
):
    try:
        module_uuid = UUID(module_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат module_id")

    module = module_repo.get_module_by_id(module_uuid)
    if not module:
        raise HTTPException(status_code=404, detail=f"Модуль с ID '{module_id}' не найден")

    if body.role_id:
        try:
            role_uuid = UUID(body.role_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Неверный формат role_id")
        role_repo.assign_role(module_uuid, role_uuid)
        roles = role_repo.fetch_module_roles(module_uuid)
        role = next((r for r in roles if str(r.id) == body.role_id), None)
        if not role:
            raise HTTPException(status_code=404, detail=f"Роль с ID '{body.role_id}' не найдена")
        return RoleResponse(id=str(role.id), name=role.name, description=role.description)

    if not body.name:
        raise HTTPException(status_code=400, detail="Необходимо указать role_id или name")

    role = role_repo.create_and_assign_role(module_uuid, body.name, body.description)
    return RoleResponse(id=str(role.id), name=role.name, description=role.description)


@router.patch("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    body: RoleUpdateRequest,
    role_repo: RoleRepository = Depends(),
):
    try:
        role_uuid = UUID(role_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат role_id")

    name = body.name.strip() if body.name is not None else None
    if body.name is not None and not name:
        raise HTTPException(status_code=400, detail="Название роли не может быть пустым")

    try:
        role = role_repo.update_role(
            role_uuid,
            name=name,
            description=body.description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return RoleResponse(id=str(role.id), name=role.name, description=role.description)


@router.delete("/modules/{module_id}/roles/{role_id}", status_code=200)
async def remove_role_from_module(
    module_id: str,
    role_id: str,
    role_repo: RoleRepository = Depends(),
    module_repo: ModuleRepository = Depends(),
):
    try:
        module_uuid = UUID(module_id)
        role_uuid = UUID(role_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат UUID")

    module = module_repo.get_module_by_id(module_uuid)
    if not module:
        raise HTTPException(status_code=404, detail=f"Модуль с ID '{module_id}' не найден")

    role_repo.unassign_role(module_uuid, role_uuid)
    return {"message": "Роль успешно удалена из модуля"}
