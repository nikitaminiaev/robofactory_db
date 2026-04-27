from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from repository.stream_repository import StreamRepository


router = APIRouter()


class RoleStreamRequest(BaseModel):
    source_role_id: str
    target_role_id: str
    name: str
    description: Optional[str] = None


class RoleStreamResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    source_role_id: str
    target_role_id: str


def _parse_uuid(value: str, field_name: str) -> UUID:
    try:
        return UUID(value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Неверный формат {field_name}")


@router.get("/modules/{module_id}/role-streams", response_model=list[RoleStreamResponse])
async def get_module_role_streams(
    module_id: str,
    stream_repo: StreamRepository = Depends(),
):
    module_uuid = _parse_uuid(module_id, "module_id")
    return stream_repo.get_module_role_streams(module_uuid)


@router.put("/modules/{module_id}/role-streams", response_model=RoleStreamResponse)
async def upsert_module_role_stream(
    module_id: str,
    body: RoleStreamRequest,
    stream_repo: StreamRepository = Depends(),
):
    module_uuid = _parse_uuid(module_id, "module_id")
    source_role_uuid = _parse_uuid(body.source_role_id, "source_role_id")
    target_role_uuid = _parse_uuid(body.target_role_id, "target_role_id")
    name = body.name.strip()

    if source_role_uuid == target_role_uuid:
        raise HTTPException(status_code=400, detail="Поток должен соединять две разные роли")
    if not name:
        raise HTTPException(status_code=400, detail="Необходимо указать название потока")

    try:
        return stream_repo.upsert_module_role_stream(
            module_uuid,
            source_role_uuid,
            target_role_uuid,
            name,
            body.description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/modules/{module_id}/role-streams/{source_role_id}/{target_role_id}", status_code=200)
async def delete_module_role_stream(
    module_id: str,
    source_role_id: str,
    target_role_id: str,
    stream_repo: StreamRepository = Depends(),
):
    module_uuid = _parse_uuid(module_id, "module_id")
    source_role_uuid = _parse_uuid(source_role_id, "source_role_id")
    target_role_uuid = _parse_uuid(target_role_id, "target_role_id")

    stream_repo.delete_module_role_stream(module_uuid, source_role_uuid, target_role_uuid)
    return {"message": "Поток успешно удален из ячейки"}
