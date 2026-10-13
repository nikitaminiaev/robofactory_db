from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from repository.module_repository import ModuleRepository
from service.freecad.part_loader import PartLoader

router = APIRouter()
_loader = PartLoader()


@router.post("/api/basic_object/{module_id}/create_cad")
async def create_cad_in_freecad(module_id: UUID, repo: ModuleRepository = Depends()):
    module = repo.get_module_with_relations_by_id(module_id)
    if not module:
        raise HTTPException(status_code=404, detail=f"Объект с ID '{module_id}' не найден")

    try:
        sent = _loader.create_empty_part_in_freecad(str(module_id), str(module.name))
        return JSONResponse({
            "success": True,
            "message": f"Команда Create CAD отправлена во FreeCAD для модуля '{module.name}'",
            "message_sent": sent
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при отправке команды Create CAD: {str(e)}")
