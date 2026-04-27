from typing import Optional, List, Dict
from pydantic import BaseModel
from .bounding_contour_dto import BoundingContourDTO


class ParentEdgeRoleDTO(BaseModel):
    parent_child_module_id: str
    parent_id: str
    role_id: Optional[str] = None
    role_name: Optional[str] = None
    role_description: Optional[str] = None


class BasicObjectDTO(BaseModel):
    id: str
    name: str
    author: str
    description: Optional[str] = None
    coordinates: Optional[Dict] = None
    role: Optional[str] = None
    role_description: Optional[str] = None
    interface_object_id: Optional[str] = None
    is_assembly: Optional[bool] = None
    is_shell: Optional[bool] = None
    bounding_contour: Optional[BoundingContourDTO] = None
    children: List[str] = []
    parents: List[str] = []
    children_counts: Dict[str, int] = {}
    parent_counts: Dict[str, int] = {}
    children_coordinates: Dict[str, Optional[dict]] = {}
    children_with_coordinates: List[dict] = []
    parent_edges: List[ParentEdgeRoleDTO] = []
    roles: List[Dict] = []
    children_roles: Dict[str, List[str]] = {}
    role_streams: List[Dict] = []
    created_ts: Optional[str] = None
    updated_ts: Optional[str] = None

    @classmethod
    def from_module(cls, module, children_counts: Optional[Dict[str, int]] = None, parent_counts: Optional[Dict[str, int]] = None):
        """
        Фабричный метод для создания DTO из модели Module.

        Args:
            module: объект Module
            children_counts: словарь {child_id: count} с количеством вхождений каждого ребёнка
            parent_counts: словарь {parent_id: count} с количеством вхождений каждого родителя
        """
        module_dict = module.to_dict()

        module_dict["children"] = [str(child["id"]) for child in module_dict.get("children", [])]
        module_dict["parents"] = [str(parent["id"]) for parent in module_dict.get("parents", [])]
        module_dict["children_counts"] = children_counts or {}
        module_dict["parent_counts"] = parent_counts or {}

        # Если есть bounding_contour, создаем для него DTO и выносим флаги на верхний уровень
        if module.bounding_contour:
            contour_dict = module.bounding_contour.to_dict()
            contour_dict["basic_object_id"] = str(module.id)
            module_dict["bounding_contour"] = BoundingContourDTO(**contour_dict)
            module_dict["is_assembly"] = contour_dict.get("is_assembly")
            module_dict["is_shell"] = contour_dict.get("is_shell")

        return cls(**module_dict)

    class Config:
        orm_mode = True