from uuid import UUID
from typing import Any, Optional, cast

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
    name: str
    description: Optional[str] = None


class RoleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None


def _role_response(role) -> RoleResponse:
    role_obj = cast(Any, role)
    return RoleResponse(
        id=str(role_obj.id),
        name=role_obj.name,
        description=role_obj.description,
    )


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
    return [_role_response(role) for role in roles]


@router.get("/roles")
async def search_roles(
    query: Optional[str] = None,
    limit: int = 20,
    role_repo: RoleRepository = Depends(),
):
    return role_repo.search_roles(query=query, limit=limit)


@router.get("/roles/{role_id}")
async def get_role_details(
    role_id: str,
    role_repo: RoleRepository = Depends(),
):
    try:
        role_uuid = UUID(role_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат role_id")

    role_details = role_repo.get_role_details(role_uuid)
    if not role_details:
        raise HTTPException(status_code=404, detail=f"Роль с ID '{role_id}' не найдена")
    return role_details


@router.patch("/roles/{role_id}")
async def update_role(
    role_id: str,
    body: RoleUpdateRequest,
    role_repo: RoleRepository = Depends(),
):
    try:
        role_uuid = UUID(role_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат role_id")

    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Название роли не может быть пустым")

    role = role_repo.update_role(role_uuid, name, body.description)
    if not role:
        raise HTTPException(status_code=404, detail=f"Роль с ID '{role_id}' не найдена")
    return role


@router.delete("/roles/{role_id}", status_code=200)
async def delete_role(
    role_id: str,
    role_repo: RoleRepository = Depends(),
):
    try:
        role_uuid = UUID(role_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат role_id")

    deleted = role_repo.delete_role(role_uuid)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Роль с ID '{role_id}' не найдена")
    return {"message": "Роль успешно удалена"}


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
        return _role_response(role)

    if not body.name:
        raise HTTPException(status_code=400, detail="Необходимо указать role_id или name")

    role = role_repo.create_and_assign_role(module_uuid, body.name, body.description)
    return _role_response(role)


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
