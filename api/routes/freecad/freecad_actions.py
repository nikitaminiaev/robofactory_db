from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from repository.module_repository import ModuleRepository
from service.freecad.part_loader import PartLoader
from utils.logger import log

router = APIRouter()

_loader = PartLoader()


@router.post("/api/basic_object/{id}/freecad/save_brep")
async def save_brep_to_freecad(id: UUID, repo: ModuleRepository = Depends()):
    """
    Отправляет команду FreeCAD экспортировать BREP активного тела и сохранить в текущий модуль.
    Координаты parent_child_module не затрагиваются.
    """
    if not repo.get_module_with_relations_by_id(id):
        raise HTTPException(status_code=404, detail=f"Объект с ID '{id}' не найден")

    try:
        sent = _loader.trigger_save_brep(str(id))
        return JSONResponse({"success": True, "message": "Команда Save BREP отправлена во FreeCAD", "message_sent": sent})
    except Exception as e:
        log(f"Ошибка при отправке Save BREP во FreeCAD: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при отправке команды: {str(e)}")


@router.post("/api/basic_object/{id}/freecad/save_position")
async def save_position_to_freecad(id: UUID, repo: ModuleRepository = Depends()):
    """
    Отправляет команду FreeCAD обновить координаты дочерних объектов сборки.

    Предварительно проверяет, что в parent_child_module существуют записи
    с parent_id = id. Если нет — команда не отправляется.
    BREP не затрагивается.
    """
    if not repo.get_module_with_relations_by_id(id):
        raise HTTPException(status_code=404, detail=f"Объект с ID '{id}' не найден")

    children_coordinates = repo.get_children_coordinates(id)
    if not children_coordinates:
        raise HTTPException(
            status_code=400,
            detail=f"Модуль '{id}' не является сборкой: в parent_child_module нет дочерних записей с parent_id='{id}'"
        )

    try:
        sent = _loader.trigger_save_position(str(id))
        return JSONResponse({"success": True, "message": "Команда Save Position отправлена во FreeCAD", "message_sent": sent})
    except Exception as e:
        log(f"Ошибка при отправке Save Position во FreeCAD: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при отправке команды: {str(e)}")


@router.post("/api/basic_object/{id}/freecad/to_supersystem")
async def to_supersystem(id: UUID, repo: ModuleRepository = Depends()):
    """
    Загружает родительский модуль во FreeCAD.

    Если родитель единственный — сразу загружает его через WebSocket.
    Если родителей несколько — возвращает предупреждение со списком ID.
    """
    basic_object = repo.get_module_with_relations_by_id(id)
    if not basic_object:
        raise HTTPException(status_code=404, detail=f"Объект с ID '{id}' не найден")

    parent_ids = [str(p.id) for p in basic_object.parents]

    if not parent_ids:
        return JSONResponse({"warning": "У данного модуля нет родителей", "parent_ids": []})

    if len(parent_ids) > 1:
        return JSONResponse({
            "warning": "Несколько родителей — выберите нужный в списке Parents ниже на странице",
            "parent_ids": parent_ids,
        })

    try:
        sent = _loader.load_part_to_freecad(id=parent_ids[0])
        return JSONResponse({
            "success": True,
            "message": "Родительский модуль загружается во FreeCAD",
            "message_sent": sent,
        })
    except Exception as e:
        log(f"Ошибка при загрузке родителя во FreeCAD: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при загрузке родителя: {str(e)}")


@router.post("/api/basic_object/{id}/freecad/to_subsystem")
async def to_subsystem(id: UUID, repo: ModuleRepository = Depends()):
    """
    Загружает дочерний модуль во FreeCAD.

    Если дочерний объект единственный — сразу загружает его через WebSocket.
    Если дочерних несколько — возвращает предупреждение со списком ID.
    """
    basic_object = repo.get_module_with_relations_by_id(id)
    if not basic_object:
        raise HTTPException(status_code=404, detail=f"Объект с ID '{id}' не найден")

    child_ids = [str(c.id) for c in basic_object.children]

    if not child_ids:
        return JSONResponse({"warning": "У данного модуля нет дочерних объектов", "child_ids": []})

    if len(child_ids) > 1:
        return JSONResponse({
            "warning": "Несколько дочерних объектов — выберите нужный в списке Children ниже на странице",
            "child_ids": child_ids,
        })

    try:
        sent = _loader.load_part_to_freecad(id=child_ids[0])
        return JSONResponse({
            "success": True,
            "message": "Дочерний модуль загружается во FreeCAD",
            "message_sent": sent,
        })
    except Exception as e:
        log(f"Ошибка при загрузке дочернего модуля во FreeCAD: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при загрузке дочернего модуля: {str(e)}")
