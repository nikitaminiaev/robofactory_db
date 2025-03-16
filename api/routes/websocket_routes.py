from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import threading
import subprocess
import os
import signal
import time
from service.web_soket_server import is_socket_server_running, get_connected_clients_count

router = APIRouter()

# Настройка шаблонов
templates = Jinja2Templates(directory="templates")

# Глобальная переменная для хранения процесса сервера
websocket_server_process = None
websocket_server_thread = None

@router.get("/websocket-test", response_class=HTMLResponse)
async def websocket_test_page(request: Request):
    """
    Отображает тестовую страницу для работы с WebSocket
    """
    return templates.TemplateResponse("websocket_test.html", {"request": request})

@router.get("/api/websocket/status")
async def get_websocket_status():
    """
    Проверяет статус WebSocket-сервера
    """
    running = is_socket_server_running()
    return JSONResponse({
        "running": running
    })

@router.get("/api/websocket/clients")
async def get_websocket_clients():
    """
    Возвращает информацию о подключенных клиентах
    """
    if not is_socket_server_running():
        return JSONResponse({
            "count": 0,
            "clients": [],
            "error": "Сервер не запущен"
        })
    
    try:
        clients_info = get_connected_clients_count()
        return JSONResponse(clients_info)
    except Exception as e:
        return JSONResponse({
            "count": 0,
            "clients": [],
            "error": f"Ошибка при получении информации о клиентах: {str(e)}"
        })

def run_server_in_thread():
    """
    Запускает WebSocket-сервер в отдельном потоке
    """
    from service.web_soket_server import start_server
    start_server()

@router.post("/api/websocket/start")
async def start_websocket_server():
    """
    Запускает WebSocket-сервер
    """
    global websocket_server_thread, websocket_server_process
    
    # Проверяем, не запущен ли уже сервер
    if is_socket_server_running():
        return JSONResponse({
            "success": True,
            "message": "Сервер уже запущен"
        })
    
    try:
        # Метод 1: Запуск в отдельном потоке (предпочтительно для разработки)
        if websocket_server_thread is None or not websocket_server_thread.is_alive():
            websocket_server_thread = threading.Thread(target=run_server_in_thread)
            websocket_server_thread.daemon = True
            websocket_server_thread.start()
            
            # Ждем немного, чтобы сервер успел запуститься
            time.sleep(1)
            
            if is_socket_server_running():
                return JSONResponse({
                    "success": True,
                    "message": "Сервер успешно запущен в отдельном потоке"
                })
            else:
                return JSONResponse({
                    "success": False,
                    "message": "Не удалось запустить сервер в отдельном потоке"
                })
        
        # Метод 2: Запуск в отдельном процессе (альтернативный вариант)
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                  "service", "web_soket_server.py")
        
        if not os.path.exists(script_path):
            # Попробуем альтернативный путь
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                     "..", "..", "service", "web_soket_server.py")
            
            if not os.path.exists(script_path):
                return JSONResponse({
                    "success": False,
                    "message": f"Файл сервера не найден: {script_path}"
                })
        
        websocket_server_process = subprocess.Popen(["python", script_path])
        
        # Ждем немного, чтобы сервер успел запуститься
        time.sleep(1)
        
        if is_socket_server_running():
            return JSONResponse({
                "success": True,
                "message": "Сервер успешно запущен в отдельном процессе"
            })
        else:
            # Если сервер не запустился, завершаем процесс
            if websocket_server_process:
                websocket_server_process.terminate()
                websocket_server_process = None
            
            return JSONResponse({
                "success": False,
                "message": "Не удалось запустить сервер"
            })
            
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"Ошибка при запуске сервера: {str(e)}"
        })

@router.post("/api/websocket/stop")
async def stop_websocket_server():
    """
    Останавливает WebSocket-сервер
    """
    global websocket_server_process
    
    if not is_socket_server_running():
        return JSONResponse({
            "success": True,
            "message": "Сервер уже остановлен"
        })
    
    try:
        # Метод 1: Если сервер запущен в отдельном процессе
        if websocket_server_process:
            websocket_server_process.terminate()
            websocket_server_process = None
        
        # Метод 2: Если сервер запущен не через наш процесс, пытаемся найти его по порту
        # Это работает только на Unix-подобных системах
        try:
            # Находим PID процесса, который слушает порт 8765
            result = subprocess.run(["lsof", "-i", ":8765", "-t"], capture_output=True, text=True)
            if result.stdout:
                pid = int(result.stdout.strip())
                os.kill(pid, signal.SIGTERM)
        except (subprocess.SubprocessError, ValueError, OSError):
            pass
        
        # Ждем немного и проверяем, остановился ли сервер
        time.sleep(1)
        
        if not is_socket_server_running():
            return JSONResponse({
                "success": True,
                "message": "Сервер успешно остановлен"
            })
        else:
            return JSONResponse({
                "success": False,
                "message": "Не удалось остановить сервер"
            })
            
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"Ошибка при остановке сервера: {str(e)}"
        }) 