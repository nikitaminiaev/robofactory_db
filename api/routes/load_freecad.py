from uuid import UUID
import json
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from repository.module_repository import ModuleRepository
from service.web_soket_server import is_socket_server_running, send_message_to_websocket
from service.freecad.function import create_cube

router = APIRouter()

@router.post("/api/basic_object/{id}/load_freecad")
async def load_object_to_freecad(request: Request, id: UUID, repo: ModuleRepository = Depends()):
    """
    Маршрут для загрузки объекта во FreeCad.
    Получает объект по ID и отправляет его данные для загрузки во FreeCad.
    """
    basic_object = repo.get_module_with_relations_by_id(id)
    if not basic_object:
        raise HTTPException(status_code=404, detail=f"Объект с ID '{id}' не найден")
    
    # Проверяем, запущен ли WebSocket-сервер
    socket_running = is_socket_server_running()
    
    # Если сервер запущен, отправляем сообщение с кодом Python
    message_sent = False
    if socket_running:
        # Отправляем JSON-объект с кодом Python для выполнения во FreeCad
        test_code = create_cube()

        message = json.dumps({
            "python_code": test_code
        })
        message_sent = send_message_to_websocket(message)
    
    
    return JSONResponse({
        "success": True,
        "message": f"Объект с ID {id} успешно отправлен во FreeCad",
        "object_id": str(id),
        "socket_server_running": socket_running,
        "message_sent": message_sent
    }) 