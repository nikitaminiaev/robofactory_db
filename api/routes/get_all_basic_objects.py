from uuid import UUID
from service import BasicObjectExtractor
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from repository.module_repository import ModuleRepository
from schemas import BasicObjectDTO

router = APIRouter()


@router.get("/api/basic_objects")
async def get_all_basic_objects(limit: int = 10, offset: int = 0, repo: ModuleRepository = Depends()):
    basic_objects = repo.get_modules_with_relations(limit=limit, offset=offset)
    
    if not basic_objects:
        raise HTTPException(status_code=404, detail="Объекты не найдены")
    
    basic_objects_dicts = [
        BasicObjectDTO.from_module(obj).model_dump()
        for obj in basic_objects
    ]
    
    return JSONResponse(content={"basic_objects": basic_objects_dicts})

@router.get("/api/basic_objects/top_level")
async def get_top_level_basic_objects(limit: int = 10, offset: int = 0, depth: int = 0, repo: ModuleRepository = Depends()):
    basic_objects = BasicObjectExtractor(repo).extract_top_level_basic_objects(limit, offset, depth)
    
    if not basic_objects:
        raise HTTPException(status_code=404, detail="Объекты не найдены")
    
    basic_objects_dicts = [
        BasicObjectDTO.from_module(obj).model_dump()
        for obj in basic_objects
    ]
    
    return JSONResponse(content={"basic_objects": basic_objects_dicts})

@router.get("/api/basic_objects/{id}/children")
async def get_children_of_basic_object(id: UUID, repo: ModuleRepository = Depends()):
    children = BasicObjectExtractor(repo).extract_children_of_basic_object(id)
    
    if not children:
        raise HTTPException(status_code=404, detail="Дети не найдены")
    
    basic_objects_dicts = [
        BasicObjectDTO.from_module(obj).model_dump()
        for obj in children
    ]
    
    return JSONResponse(content={"basic_objects": basic_objects_dicts})
    

@router.get("/api/basic_objects/count")
async def get_count_of_basic_objects(repo: ModuleRepository = Depends()):
    count = repo.get_count_of_modules()

    return count
