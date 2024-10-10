from fastapi import APIRouter, Depends, HTTPException
from repository.basic_repository import BasicObjectRepository

router = APIRouter()


@router.get("/basic_objects")
def get_all_basic_objects(repo: BasicObjectRepository = Depends()):
    basic_objects = repo.get_all_basic_objects()
    if not basic_objects:
        raise HTTPException(status_code=404, detail="Объекты не найдены")
    return basic_objects
