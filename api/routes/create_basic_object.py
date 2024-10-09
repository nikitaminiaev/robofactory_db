from fastapi import APIRouter, Depends
from pydantic import BaseModel
from repository.basic_repository import BasicObjectRepository

router = APIRouter()

class BasicObjectCreate(BaseModel):
    name: str
    description: str = None
    coordinates: dict = None
    parent_role: str = None
    role_description: str = None

@router.post("/basic_object/")
def create_basic_object(item: BasicObjectCreate, repo: BasicObjectRepository = Depends()):
    return repo.create_basic_object(**item.model_dump())