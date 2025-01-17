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

    @classmethod
    def from_module(cls, module):
        """
        Фабричный метод для создания DTO из модели Module
        """
        module_dict = module.to_dict()
        
        module_dict["children"] = [str(child["id"]) for child in module_dict.get("children", [])]
        module_dict["parents"] = [str(parent["id"]) for parent in module_dict.get("parents", [])]
        
        # Если есть bounding_contour, создаем для него DTO
        if module.bounding_contour:
            contour_dict = module.bounding_contour.to_dict()
            contour_dict["basic_object_id"] = str(module.id) 
            module_dict["bounding_contour"] = BoundingContourDTO(**contour_dict)

        return cls(**module_dict)

    class Config:
        orm_mode = True 