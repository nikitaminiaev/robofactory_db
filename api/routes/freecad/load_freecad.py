from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from repository.module_repository import ModuleRepository
from service.freecad.part_loader import PartLoader
from service.freecad.hierarchy_loader import HierarchyLoader
from utils.logger import log

router = APIRouter()

part_loader = PartLoader()


class ChildDepth(BaseModel):
    child_id: str
    parent_child_module_id: Optional[str] = None
    depth: int = 1


class LoadFreeCadRequest(BaseModel):
    child_depths: List[ChildDepth] = []


@router.post("/api/basic_object/{id}/load_freecad")
async def load_object_to_freecad(request: Request, id: UUID, repo: ModuleRepository = Depends()):
    """
    Маршрут для загрузки объекта во FreeCad.
    Получает объект по ID и отправляет его данные для загрузки во FreeCad.
    
    Тело запроса может содержать:
    - child_depths: массив объектов {child_id, parent_child_module_id, depth} для настройки глубины загрузки каждого ребенка
    
    При глубине > 1 вычисляет абсолютные координаты для каждого уровня вложенности.
    """
    try:
        body = await request.json()
        child_depths = body.get('child_depths', []) if body else []
        
        hierarchy_loader = HierarchyLoader(repo)
        absolute_coordinates = hierarchy_loader.get_hierarchy_with_absolute_coordinates(
            root_id=id,
            child_depths=child_depths
        )
        
        message_sent = part_loader.load_part_to_freecad(
            id=str(id),
            child_depths=child_depths,
            absolute_coordinates=absolute_coordinates
        )
        
        return JSONResponse({
            "success": True,
            "message": f"Объект с ID {id} успешно отправлен во FreeCad",
            "object_id": str(id),
            "message_sent": message_sent
        })
        
    except HTTPException:
        raise
    except Exception as e:
        log(f"Ошибка при загрузке объекта во FreeCad: {e}")
        return JSONResponse({
            "success": False,
            "message": f"Ошибка при загрузке объекта во FreeCad: {str(e)}",
            "object_id": str(id)
        }, status_code=500)