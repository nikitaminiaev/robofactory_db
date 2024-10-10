from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from repository.basic_repository import BasicObjectRepository

router = APIRouter()


class BasicObjectCreate(BaseModel):
    name: str
    author: str
    description: str = None
    coordinates: dict = None
    role: str = None
    role_description: str = None


@router.post("/api/basic_object/")
def create_basic_object(item: BasicObjectCreate, repo: BasicObjectRepository = Depends()):
    existing_object = repo.get_basic_object(item.name)
    if existing_object:
        raise HTTPException(status_code=400, detail="Объект с таким именем уже существует")
    repo.create_basic_object(**item.model_dump())

    return {"ok": True}
