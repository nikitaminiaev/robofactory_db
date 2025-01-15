from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from repository.module_repository import ModuleRepository
from schemas import BasicObjectDTO


router = APIRouter()


@router.get("/api/basic_object", response_model=BasicObjectDTO)
def get_basic_object(request: Request, name: str = None, repo: ModuleRepository = Depends()):
    error_message = None
    basic_object = None

    if name:
        basic_object = repo.get_module_with_relations(name)
        if not basic_object:
            error_message = f"Объект с именем '{name}' не найден"

    if basic_object:
        return BasicObjectDTO(**basic_object.to_dict())
    else:
        return JSONResponse({
            "basic_object": None,
            "error_message": error_message,
            "search_performed": name is not None
        })


@router.get("/api/basic_object/{id}", response_model=BasicObjectDTO)
def get_basic_object_by_id(request: Request, id: UUID, repo: ModuleRepository = Depends()):
    basic_object = repo.get_module_with_relations_by_id(id)
    if not basic_object:
        raise HTTPException(status_code=404, detail=f"Объект с ID '{id}' не найден")

    return BasicObjectDTO(**basic_object.to_dict())


@router.get("/api/basic_object/{id}/parent_ids", response_model=List[str])
def get_basic_object_parents(request: Request, id: UUID, repo: ModuleRepository = Depends()):
    basic_object = repo.get_module_with_relations_by_id(id)
    if not basic_object:
        raise HTTPException(status_code=404, detail=f"Объект с ID '{id}' не найден")
    # todo так плохо делать, нужен отдельный метод репо для парентов
    return basic_object.to_dict()['parents']

