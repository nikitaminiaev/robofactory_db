from typing import Optional, List, Dict
from pydantic import BaseModel
from .bounding_contour_dto import BoundingContourDTO

class BasicObjectDTO(BaseModel):
    id: str
    name: str
    author: str
    description: Optional[str] = None
    coordinates: Optional[Dict] = None
    role: Optional[str] = None
    role_description: Optional[str] = None
    interface_object_id: Optional[str] = None
    bounding_contour: Optional[BoundingContourDTO] = None
    children: List[str] = []
    parents: List[str] = []
    created_ts: Optional[str] = None
    updated_ts: Optional[str] = None

    class Config:
        orm_mode = True 