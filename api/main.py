from routes.freecad import load_freecad
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from routes import get_all_basic_objects, get_basic_object, create_basic_object
from routes import websocket_routes
import threading
from service.web_soket_server import get_server_instance

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(get_all_basic_objects.router)
app.include_router(get_basic_object.router)
app.include_router(create_basic_object.router)
app.include_router(load_freecad.router)
app.include_router(websocket_routes.router)

# Функция для запуска WebSocket-сервера в отдельном потоке
def start_websocket_server_thread():
    server = get_server_instance()
    print("Автоматический запуск WebSocket-сервера...")
    server.start()

# Запускаем WebSocket-сервер при старте приложения
@app.on_event("startup")
async def startup_event():
    print("Приложение запускается, инициализация WebSocket-сервера...")
    # Проверяем, не запущен ли уже сервер
    server = get_server_instance()
    if not server.is_running():
        # Запускаем сервер в отдельном потоке
        websocket_thread = threading.Thread(target=start_websocket_server_thread)
        websocket_thread.daemon = True  # Поток будет автоматически завершен при выходе из программы
        websocket_thread.start()
        print("WebSocket-сервер запускается в фоновом режиме")
    else:
        print("WebSocket-сервер уже запущен")

# Останавливаем WebSocket-сервер при завершении работы приложения
@app.on_event("shutdown")
async def shutdown_event():
    print("Приложение завершает работу, остановка WebSocket-сервера...")
    server = get_server_instance()
    server.stop()
    print("WebSocket-сервер остановлен")

@app.get("/")
def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/basic_object")
async def root(request: Request):
    return templates.TemplateResponse("basic_object_search.html", {"request": request})

@app.get("/basic_object/{id}")
async def basic_object_details(request: Request, id: str):
    return templates.TemplateResponse("basic_object_details.html", {"request": request, "id": id})