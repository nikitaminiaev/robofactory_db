from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from repository import InterfaceRepository, InterfaceMappingRepository
from schemas.interface_object_dto import (
    InterfaceObjectDTO,
    InterfaceCreateDTO,
    InterfaceUpdateDTO,
    InterfaceMappingDTO,
    InterfaceMappingCreateDTO,
)

router = APIRouter()


def _parse_uuid(value: str, field_name: str) -> UUID:
    try:
        return UUID(value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Неверный формат {field_name}")


@router.get("/api/modules/{module_id}/interfaces", response_model=List[InterfaceObjectDTO])
async def get_module_interfaces(
    module_id: str,
    interface_repo: InterfaceRepository = Depends(),
):
    module_uuid = _parse_uuid(module_id, "module_id")
    interfaces = interface_repo.get_module_interfaces(module_uuid)
    return [InterfaceObjectDTO(**i) for i in interfaces]


@router.post("/api/modules/{module_id}/interfaces", response_model=InterfaceObjectDTO, status_code=201)
async def create_module_interface(
    module_id: str,
    body: InterfaceCreateDTO,
    interface_repo: InterfaceRepository = Depends(),
):
    module_uuid = _parse_uuid(module_id, "module_id")
    try:
        iface = interface_repo.create_interface(
            module_id=module_uuid,
            name=body.name,
            direction=body.direction,
            physical_form=body.physical_form,
            parameters=body.parameters,
            is_mandatory=body.is_mandatory,
            is_service=body.is_service,
            description=body.description,
            ttx=body.ttx,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return InterfaceObjectDTO(**iface)


@router.patch("/api/modules/{module_id}/interfaces/{interface_id}", response_model=InterfaceObjectDTO)
async def update_module_interface(
    module_id: str,
    interface_id: str,
    body: InterfaceUpdateDTO,
    interface_repo: InterfaceRepository = Depends(),
):
    module_uuid = _parse_uuid(module_id, "module_id")
    iface_uuid = _parse_uuid(interface_id, "interface_id")
    try:
        iface = interface_repo.update_interface(
            interface_id=iface_uuid,
            module_id=module_uuid,
            name=body.name,
            direction=body.direction,
            physical_form=body.physical_form,
            parameters=body.parameters,
            is_mandatory=body.is_mandatory,
            is_service=body.is_service,
            description=body.description,
            ttx=body.ttx,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not iface:
        raise HTTPException(status_code=404, detail=f"Интерфейс с ID '{interface_id}' не найден")
    return InterfaceObjectDTO(**iface)


@router.delete("/api/modules/{module_id}/interfaces/{interface_id}", status_code=200)
async def delete_module_interface(
    module_id: str,
    interface_id: str,
    interface_repo: InterfaceRepository = Depends(),
):
    module_uuid = _parse_uuid(module_id, "module_id")
    iface_uuid = _parse_uuid(interface_id, "interface_id")
    deleted = interface_repo.delete_interface(iface_uuid, module_uuid)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Интерфейс с ID '{interface_id}' не найден")
    return {"message": "Интерфейс успешно удален"}


@router.get("/api/modules/{module_id}/interface-mappings", response_model=List[InterfaceMappingDTO])
async def get_module_mappings(
    module_id: str,
    mapping_repo: InterfaceMappingRepository = Depends(),
):
    module_uuid = _parse_uuid(module_id, "module_id")
    mappings = mapping_repo.get_module_mappings(module_uuid)
    return [InterfaceMappingDTO(**m) for m in mappings]


@router.post("/api/modules/{module_id}/interface-mappings", response_model=InterfaceMappingDTO, status_code=201)
async def create_interface_mapping(
    module_id: str,
    body: InterfaceMappingCreateDTO,
    mapping_repo: InterfaceMappingRepository = Depends(),
):
    module_uuid = _parse_uuid(module_id, "module_id")
    role_port_uuid = _parse_uuid(body.role_port_id, "role_port_id")
    interface_uuid = _parse_uuid(body.interface_id, "interface_id")
    try:
        mapping = mapping_repo.create_mapping(module_uuid, role_port_uuid, interface_uuid)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return InterfaceMappingDTO(**mapping)


@router.delete("/api/modules/{module_id}/interface-mappings/{mapping_id}", status_code=200)
async def delete_interface_mapping(
    module_id: str,
    mapping_id: str,
    mapping_repo: InterfaceMappingRepository = Depends(),
):
    module_uuid = _parse_uuid(module_id, "module_id")
    mapping_uuid = _parse_uuid(mapping_id, "mapping_id")
    deleted = mapping_repo.delete_mapping(mapping_uuid, module_uuid)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Маппинг с ID '{mapping_id}' не найден")
    return {"message": "Маппинг успешно удален"}


@router.get("/api/role-ports/{port_id}/interface-mappings", response_model=List[InterfaceMappingDTO])
async def get_role_port_interface_mappings(
    port_id: str,
    mapping_repo: InterfaceMappingRepository = Depends(),
):
    port_uuid = _parse_uuid(port_id, "port_id")
    mappings = mapping_repo.get_role_port_mappings(port_uuid)
    return [InterfaceMappingDTO(**m) for m in mappings]
