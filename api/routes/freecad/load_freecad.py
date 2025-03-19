from uuid import UUID
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from repository.module_repository import ModuleRepository
from dto.freecad.basic_object import BasicObject
from service.freecad.part_loader import PartLoader

router = APIRouter()

# Создаем экземпляр PartLoader для использования в маршруте
part_loader = PartLoader()

@router.post("/api/basic_object/{id}/load_freecad")
async def load_object_to_freecad(request: Request, id: UUID, repo: ModuleRepository = Depends()):
    """
    Маршрут для загрузки объекта во FreeCad.
    Получает объект по ID и отправляет его данные для загрузки во FreeCad.
    """
    try:
        basic_object = repo.get_module_with_relations_by_id(id)
        if not basic_object:
            raise HTTPException(status_code=404, detail=f"Объект с ID '{id}' не найден")
        
        basic_object_dto = BasicObject.from_module(basic_object)
        
        message_sent = part_loader.load_part_to_freecad(basic_object_dto)
        
        return JSONResponse({
            "success": True,
            "message": f"Объект с ID {id} успешно отправлен во FreeCad",
            "object_id": str(id),
            "object_name": basic_object_dto.name,
            "message_sent": message_sent
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка при загрузке объекта во FreeCad: {e}")
        return JSONResponse({
            "success": False,
            "message": f"Ошибка при загрузке объекта во FreeCad: {str(e)}",
            "object_id": str(id)
        }, status_code=500) 