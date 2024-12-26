from typing import Optional, Dict
from pydantic import BaseModel


class BoundingContourDTO(BaseModel):
    id: str
    basic_object_id: str
    is_assembly: bool
    brep_files: Dict[str, str]
    parent_id: Optional[str] = None
    created_ts: Optional[str] = None
    updated_ts: Optional[str] = None

    class Config:
        orm_mode = True 