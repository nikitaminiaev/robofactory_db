from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from repository.module_repository import ModuleRepository
from schemas import BasicObjectDTO

router = APIRouter()


@router.get("/api/basic_objects")
def get_all_basic_objects(repo: ModuleRepository = Depends()):
    basic_objects = repo.get_all_modules()
    if not basic_objects:
        raise HTTPException(status_code=404, detail="Объекты не найдены")

    basic_objects_dicts = [
        BasicObjectDTO.from_module(obj).model_dump()  # или .dict() для Pydantic v1
        for obj in basic_objects
    ]

    return JSONResponse(content={"basic_objects": basic_objects_dicts})
