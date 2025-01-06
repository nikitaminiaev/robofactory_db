from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from api.repository.module_repository import ModuleRepository

router = APIRouter()


@router.get("/api/basic_objects")
def get_all_basic_objects(repo: ModuleRepository = Depends()):
    basic_objects = repo.get_all_basic_objects()
    if not basic_objects:
        raise HTTPException(status_code=404, detail="Объекты не найдены")
    basic_objects_dicts = [obj.to_dict() for obj in basic_objects]

    return JSONResponse(content={"basic_objects": basic_objects_dicts})
