from uuid import UUID
from typing import List, Dict, Optional

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from repository.module_repository import ModuleRepository
from schemas import BasicObjectDTO


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

    return BasicObjectDTO.from_module(basic_object)


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

