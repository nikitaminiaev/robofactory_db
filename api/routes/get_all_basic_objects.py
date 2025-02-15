from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from repository.module_repository import ModuleRepository
from schemas import BasicObjectDTO

router = APIRouter()


@router.get("/api/basic_objects")
def get_all_basic_objects(limit: int = 10, offset: int = 0, repo: ModuleRepository = Depends()):
    basic_objects = repo.get_modules_with_relations(limit=limit, offset=offset)
    
    if not basic_objects:
        raise HTTPException(status_code=404, detail="Объекты не найдены")
    
    basic_objects_dicts = [
        BasicObjectDTO.from_module(obj).model_dump()
        for obj in basic_objects
    ]
    
    return JSONResponse(content={"basic_objects": basic_objects_dicts})

@router.get("/api/basic_objects/count")
def get_count_of_basic_objects(repo: ModuleRepository = Depends()):
    count = repo.get_count_of_modules()

    return count
