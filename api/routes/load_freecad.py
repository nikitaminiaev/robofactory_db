from uuid import UUID
import json
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from repository.module_repository import ModuleRepository
from service.web_soket_server import get_server_instance
from service.freecad.function import create_cube

router = APIRouter()

@router.post("/api/basic_object/{id}/load_freecad")
async def load_object_to_freecad(request: Request, id: UUID, repo: ModuleRepository = Depends()):
    """
    Маршрут для загрузки объекта во FreeCad.
    Получает объект по ID и отправляет его данные для загрузки во FreeCad.
    """
    try:
        # Получаем объект из репозитория
        basic_object = repo.get_module_with_relations_by_id(id)
        if not basic_object:
            raise HTTPException(status_code=404, detail=f"Объект с ID '{id}' не найден")
        
        # Получаем экземпляр WebSocket-сервера
        server = get_server_instance()
        
        # Проверяем, запущен ли WebSocket-сервер
        socket_running = server.is_running()
        
        # Если сервер запущен, отправляем сообщение с кодом Python
        message_sent = False
        
        if socket_running:
            # Отправляем JSON-объект с кодом Python для выполнения во FreeCad
            test_code = create_cube()
            
            # Добавляем информацию об объекте в сообщение
            message = json.dumps({
                "python_code": test_code,
                "object_id": str(id),
                "object_name": getattr(basic_object, "name", "Unknown")
            })
            
            message_sent = server.send_message(message)
        
        # Формируем ответ с более детальной информацией
        return JSONResponse({
            "success": True,
            "message": f"Объект с ID {id} успешно отправлен во FreeCad",
            "object_id": str(id),
            "object_name": getattr(basic_object, "name", "Unknown"),
            "socket_server_running": socket_running,
            "message_sent": message_sent
        })
        
    except HTTPException:
        # Пробрасываем HTTP исключения дальше
        raise
    except Exception as e:
        # Обрабатываем другие исключения
        print(f"Ошибка при загрузке объекта во FreeCad: {e}")
        return JSONResponse({
            "success": False,
            "message": f"Ошибка при загрузке объекта во FreeCad: {str(e)}",
            "object_id": str(id)
        }, status_code=500) 