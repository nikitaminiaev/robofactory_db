from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import threading
import subprocess
import os
import signal
import time
from service.web_soket_server import get_server_instance

router = APIRouter()

# Настройка шаблонов
templates = Jinja2Templates(directory="templates")

# Глобальная переменная для хранения процесса сервера
websocket_server_process = None
websocket_server_thread = None

@router.get("/websocket-server", response_class=HTMLResponse)
async def websocket_test_page(request: Request):
    """
    Отображает тестовую страницу для работы с WebSocket
    """
    return templates.TemplateResponse("websocket_server.html", {"request": request})

@router.get("/api/websocket/status")
async def get_websocket_status():
    """
    Проверяет статус WebSocket-сервера
    """
    server = get_server_instance()
    running = server.is_running()
    return JSONResponse({
        "running": running
    })

@router.get("/api/websocket/clients")
async def get_websocket_clients():
    """
    Возвращает информацию о подключенных клиентах
    """
    server = get_server_instance()
    if not server.is_running():
        return JSONResponse({
            "count": 0,
            "clients": [],
            "error": "Сервер не запущен"
        })
    
    try:
        clients_info = server.get_connected_clients_count()
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
    try:
        server = get_server_instance()
        print("Запуск WebSocket-сервера в потоке...")
        server.start()
    except Exception as e:
        print(f"Ошибка при запуске WebSocket-сервера в потоке: {e}")
        # Логируем всю трассировку стека для отладки
        import traceback
        traceback.print_exc()

@router.post("/api/websocket/start")
async def start_websocket_server():
    """
    Запускает WebSocket-сервер
    """
    global websocket_server_thread, websocket_server_process
    
    server = get_server_instance()
    
    # Проверяем, не запущен ли уже сервер
    if server.is_running():
        return JSONResponse({
            "success": True,
            "message": "Сервер уже запущен"
        })
    
    try:
        # Метод 1: Запуск в отдельном потоке (предпочтительно для разработки)
        if websocket_server_thread is None or not websocket_server_thread.is_alive():
            # Остановим сервер на всякий случай перед запуском
            try:
                server.stop()
            except Exception as e:
                print(f"Ошибка при остановке сервера перед перезапуском: {e}")
                
            # Запускаем новый поток
            websocket_server_thread = threading.Thread(target=run_server_in_thread)
            websocket_server_thread.daemon = True
            websocket_server_thread.start()
            
            # Ждем немного, чтобы сервер успел запуститься
            retries = 3
            for i in range(retries):
                time.sleep(1)
                if server.is_running():
                    return JSONResponse({
                        "success": True,
                        "message": f"Сервер успешно запущен в отдельном потоке (попытка {i+1})"
                    })
                print(f"Ожидание запуска сервера, попытка {i+1}/{retries}...")
            
            # Если сервер не запустился, но поток всё ещё выполняется, даем ему еще шанс
            if websocket_server_thread.is_alive():
                return JSONResponse({
                    "success": False,
                    "message": "Сервер запускается, но еще не готов принимать соединения. Попробуйте проверить статус позже."
                })
            else:
                return JSONResponse({
                    "success": False,
                    "message": "Не удалось запустить сервер в отдельном потоке. Поток завершился преждевременно."
                })
        
        # Метод 2: Запуск в отдельном процессе (альтернативный вариант)
        # Останавливаем предыдущий процесс, если он существует
        if websocket_server_process:
            try:
                websocket_server_process.terminate()
                websocket_server_process = None
                time.sleep(1)  # Даем время на завершение
            except Exception as e:
                print(f"Ошибка при остановке предыдущего процесса: {e}")
        
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
        
        print(f"Запуск WebSocket-сервера из файла: {script_path}")
        
        # Запускаем процесс с перенаправлением вывода для логирования
        try:
            websocket_server_process = subprocess.Popen(
                ["python", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Ждем немного, чтобы сервер успел запуститься
            retries = 3
            for i in range(retries):
                time.sleep(1)
                if server.is_running():
                    return JSONResponse({
                        "success": True,
                        "message": f"Сервер успешно запущен в отдельном процессе (попытка {i+1})"
                    })
                print(f"Ожидание запуска сервера в отдельном процессе, попытка {i+1}/{retries}...")
                
                # Проверяем, не завершился ли процесс с ошибкой
                if websocket_server_process.poll() is not None:
                    stdout, stderr = websocket_server_process.communicate()
                    return JSONResponse({
                        "success": False,
                        "message": f"Процесс сервера завершился с ошибкой. Код: {websocket_server_process.returncode}",
                        "stdout": stdout,
                        "stderr": stderr
                    })
            
            # Если сервер не запустился, завершаем процесс
            if websocket_server_process and websocket_server_process.poll() is None:
                websocket_server_process.terminate()
                stdout, stderr = websocket_server_process.communicate()
                websocket_server_process = None
                
                return JSONResponse({
                    "success": False,
                    "message": "Не удалось запустить сервер в отдельном процессе после нескольких попыток",
                    "stdout": stdout,
                    "stderr": stderr
                })
            
        except Exception as e:
            if websocket_server_process and websocket_server_process.poll() is None:
                websocket_server_process.terminate()
                websocket_server_process = None
                
            return JSONResponse({
                "success": False,
                "message": f"Ошибка при запуске процесса: {str(e)}"
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
    global websocket_server_process, websocket_server_thread
    
    server = get_server_instance()
    
    # Проверяем, запущен ли сервер
    if not server.is_running():
        return JSONResponse({
            "success": True,
            "message": "Сервер уже остановлен"
        })
    
    try:
        stop_methods_used = []
        
        # Метод 1: Если сервер запущен в отдельном процессе, завершаем его
        if websocket_server_process and websocket_server_process.poll() is None:
            try:
                websocket_server_process.terminate()
                websocket_server_process.wait(timeout=3)  # Ждем завершения процесса с таймаутом
                stop_methods_used.append("завершение процесса")
            except Exception as e:
                print(f"Ошибка при остановке процесса: {e}")
                # Принудительно завершаем процесс
                try:
                    websocket_server_process.kill()
                    stop_methods_used.append("принудительное завершение процесса")
                except Exception as e2:
                    print(f"Ошибка при принудительной остановке процесса: {e2}")
            finally:
                websocket_server_process = None
        
        # Метод 2: Используем метод stop() экземпляра сервера
        try:
            server.stop()
            stop_methods_used.append("остановка через API")
        except Exception as e:
            print(f"Ошибка при остановке сервера через API: {e}")
        
        # Метод 3: Пытаемся остановить поток, если он запущен
        if websocket_server_thread and websocket_server_thread.is_alive():
            # В Python нельзя принудительно остановить поток, но можно сделать 
            # его демоном, чтобы он завершался при завершении основного процесса
            websocket_server_thread.daemon = True
            # Отмечаем, что пытались работать с потоком
            stop_methods_used.append("пометка потока как демона")
        
        # Метод 4: Если сервер запущен не через наш процесс, пытаемся найти его по порту
        # Это работает только на Unix-подобных системах
        try:
            # Находим PID процесса, который слушает порт 8765
            result = subprocess.run(["lsof", "-i", ":8765", "-t"], capture_output=True, text=True)
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid_str in pids:
                    try:
                        pid = int(pid_str)
                        os.kill(pid, signal.SIGTERM)
                        print(f"Отправлен SIGTERM процессу {pid}")
                        stop_methods_used.append(f"завершение процесса {pid} по PID")
                    except (ValueError, OSError, ProcessLookupError) as e:
                        print(f"Ошибка при остановке процесса {pid_str}: {e}")
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"Ошибка при поиске процесса по порту: {e}")
        
        # Ждем немного и проверяем, остановился ли сервер
        time.sleep(2)
        
        if not server.is_running():
            return JSONResponse({
                "success": True,
                "message": f"Сервер успешно остановлен (использованы методы: {', '.join(stop_methods_used)})"
            })
        else:
            # Последняя попытка - жесткое завершение
            try:
                # Пытаемся найти и завершить процесс с помощью SIGKILL (Unix-системы)
                result = subprocess.run(["lsof", "-i", ":8765", "-t"], capture_output=True, text=True)
                if result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid_str in pids:
                        try:
                            pid = int(pid_str)
                            os.kill(pid, signal.SIGKILL)
                            print(f"Отправлен SIGKILL процессу {pid}")
                            stop_methods_used.append(f"принудительное завершение процесса {pid}")
                        except (ValueError, OSError) as e:
                            print(f"Ошибка при принудительной остановке процесса {pid_str}: {e}")
            except Exception as e:
                print(f"Ошибка при принудительной остановке сервера: {e}")
            
            # Финальная проверка
            time.sleep(1)
            if not server.is_running():
                return JSONResponse({
                    "success": True,
                    "message": f"Сервер успешно остановлен после принудительного завершения (использованы методы: {', '.join(stop_methods_used)})"
                })
            else:
                return JSONResponse({
                    "success": False,
                    "message": f"Не удалось полностью остановить сервер. Использованные методы: {', '.join(stop_methods_used)}"
                })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "message": f"Ошибка при остановке сервера: {str(e)}"
        }) 