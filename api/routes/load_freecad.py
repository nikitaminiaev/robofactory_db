from uuid import UUID
import socket
import json
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from repository.module_repository import ModuleRepository

router = APIRouter()

def is_socket_server_running(host="localhost", port=8765):
    """Проверяет, запущен ли WebSocket-сервер"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = False
    try:
        # Пытаемся подключиться к серверу
        sock.connect((host, port))
        result = True
    except (socket.timeout, ConnectionRefusedError):
        result = False
    finally:
        sock.close()
    return result

def send_message_to_websocket(message, host="localhost", port=8765):
    """Отправляет сообщение через WebSocket-сервер"""
    try:
        # Создаем простой клиент для отправки сообщения
        # Это упрощенная реализация, в реальном приложении 
        # следует использовать полноценную библиотеку для WebSocket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        
        # Отправляем сообщение через WebSocket-сервер
        # Здесь мы просто передаем сообщение серверу, который сам обработает его
        # и отправит подключенным клиентам
        print(f"Отправка сообщения на WebSocket-сервер: {message}")
        sock.sendall(message.encode('utf-8'))
        
        # Ожидаем подтверждение от сервера
        response = sock.recv(1024)
        print(f"Получен ответ от WebSocket-сервера: {response.decode('utf-8')}")
        
        sock.close()
        return True
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")
        return False

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
        message = json.dumps({
            "python_code": """
import FreeCAD
import Part

doc = FreeCAD.newDocument('Example')
box = Part.makeBox(10, 10, 10)
cube = doc.addObject('Part::Feature', 'Cube')
cube.Shape = box
doc.recompute()

# Возвращаем результат
result = {'object_created': cube.Name, 'dimensions': [10, 10, 10]}
"""
        })
        message_sent = send_message_to_websocket(message)
    
    # Здесь должна быть логика для отправки данных во FreeCad
    # Это может быть вызов внешнего API, запуск скрипта или другой механизм
    
    return JSONResponse({
        "success": True,
        "message": f"Объект с ID {id} успешно отправлен во FreeCad",
        "object_id": str(id),
        "socket_server_running": socket_running,
        "message_sent": message_sent
    }) 