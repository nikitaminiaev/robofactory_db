from uuid import UUID

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from repository.basic_repository import BasicObjectRepository


router = APIRouter()


@router.get("/api/basic_object")
def get_basic_object(request: Request, name: str = None, repo: BasicObjectRepository = Depends()):
    error_message = None
    basic_object = None

    if name:
        basic_object = repo.get_basic_object_with_relations(name)
        if not basic_object:
            error_message = f"Объект с именем '{name}' не найден"

    return JSONResponse({
        "basic_object": basic_object.to_dict() if basic_object else None,
        "error_message": error_message,
        "search_performed": name is not None
    })


@router.get("/api/basic_object/{id}")
def get_basic_object_by_id(request: Request, id: UUID, repo: BasicObjectRepository = Depends()):
    basic_object = repo.get_basic_object_with_relations_by_id(id)
    if not basic_object:
        raise HTTPException(status_code=404, detail=f"Объект с ID '{id}' не найден")

    return JSONResponse(basic_object.to_dict())

@router.get("/api/basic_object/{id}/parent_ids")
def get_basic_object_by_id(request: Request, id: UUID, repo: BasicObjectRepository = Depends()):
    basic_object = repo.get_basic_object_with_relations_by_id(id)
    if not basic_object:
        raise HTTPException(status_code=404, detail=f"Объект с ID '{id}' не найден")
    #todo так плохо делать, нужен отдельный метод репо для парентов
    return JSONResponse(basic_object.to_dict()['parents'])

