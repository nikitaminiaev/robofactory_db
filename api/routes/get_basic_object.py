from uuid import UUID
from typing import List, Dict, Optional

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from repository.module_repository import ModuleRepository
from schemas import BasicObjectDTO
from schemas.basic_object_dto import ParentEdgeRoleDTO


router = APIRouter()


@router.get("/api/basic_object", response_model=List[BasicObjectDTO])
async def get_basic_object(
    request: Request, 
    name: Optional[str] = None, 
    author: Optional[str] = None, 
    created_ts: Optional[str] = None,
    repo: ModuleRepository = Depends()
):
    if name or author or created_ts:
        modules = repo.get_module_with_relations(name=name, author=author, created_ts=created_ts)
        return [BasicObjectDTO.from_module(m) for m in modules]
    
    return []


@router.get("/api/basic_object/{id}", response_model=BasicObjectDTO)
async def get_basic_object_by_id(request: Request, id: UUID, repo: ModuleRepository = Depends()):
    basic_object = repo.get_module_with_relations_by_id(id)
    if not basic_object:
        raise HTTPException(status_code=404, detail=f"Объект с ID '{id}' не найден")

    children_counts = repo.get_child_counts(id)
    parent_counts = repo.get_parent_counts(id)
    children_roles = repo.get_children_roles(id)
    parent_edges = repo.get_parent_edges_with_roles(id)
    result = BasicObjectDTO.from_module(basic_object, children_counts=children_counts, parent_counts=parent_counts)
    result.children_roles = children_roles
    result.parent_edges = [ParentEdgeRoleDTO(**edge) for edge in parent_edges]

    if result.bounding_contour:
        if hasattr(result.bounding_contour.brep_files, 'get'):
            result.bounding_contour.brep_files.get('brep_string', 'NOT_FOUND')

    # Добавляем координаты дочерних объектов из parent_child_module.
    # Плагин FreeCAD использует их при загрузке сборки для расстановки Placement.
    # children_coordinates - словарь (уникальные children)
    children_with_coords = repo.get_children_coordinates(id)
    if result.children:
        result.children_coordinates = {item["child_id"]: item["coordinates"] for item in children_with_coords}

    # Добавляем полный список записей children с координатами (включая дубликаты)
    result.children_with_coordinates = children_with_coords

    return result


@router.delete("/api/basic_object/{id}")
async def delete_basic_object(request: Request, id: UUID, repo: ModuleRepository = Depends()):
    try:
        repo.delete_module(id)
        return JSONResponse(content={"message": "Модуль успешно удален"}, status_code=200)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении модуля: {str(e)}")


@router.get("/api/basic_object/{id}/parent_ids", response_model=List[str])
async def get_basic_object_parents(request: Request, id: UUID, repo: ModuleRepository = Depends()):
    basic_object = repo.get_module_with_relations_by_id(id)
    if not basic_object:
        raise HTTPException(status_code=404, detail=f"Объект с ID '{id}' не найден")
    
    return [str(parent.id) for parent in basic_object.parents]


class ModuleIdsRequest(BaseModel):
    ids: List[str]

@router.post("/api/basic_objects/names", response_model=Dict[str, str])
async def get_modules_names(request: ModuleIdsRequest, repo: ModuleRepository = Depends()):
    """
    Получение имен объектов по списку их идентификаторов
    
    Args:
        request: объект запроса со списком идентификаторов
        repo: репозиторий модулей
        
    Returns:
        словарь вида {id: name}
    """
    try:
        if not request.ids:
            return {}
            
        valid_uuids = []
        for id_str in request.ids:
            try:
                valid_uuids.append(UUID(id_str))
            except ValueError:
                continue
        
        names_dict = repo.get_modules_names_by_ids(valid_uuids)
        
        return names_dict
    except Exception as e:
        print(f"Ошибка при получении имен модулей: {str(e)}")
        return {}

