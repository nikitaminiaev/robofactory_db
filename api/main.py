from routes.freecad import load_freecad, freecad_actions, create_cad
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from routes import get_all_basic_objects, get_basic_object, create_basic_object
from routes import websocket_routes, copy_module, module_versions, brep_files, cad_agent_proxy, module_files
from routes import module_roles, module_streams
import threading
from service.web_soket_server import get_server_instance

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(get_all_basic_objects.router)
app.include_router(get_basic_object.router)
app.include_router(create_basic_object.router)
app.include_router(load_freecad.router)
app.include_router(freecad_actions.router)
app.include_router(create_cad.router)
app.include_router(websocket_routes.router)
app.include_router(copy_module.router, prefix="/api")
app.include_router(module_versions.router, prefix="/api")
app.include_router(brep_files.router, prefix="/api")
app.include_router(cad_agent_proxy.router, prefix="/api")
app.include_router(module_files.router, prefix="/api")
app.include_router(module_roles.router, prefix="/api")
app.include_router(module_streams.router, prefix="/api")

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
def root_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/basic_object")
async def basic_object_page(request: Request):
    return templates.TemplateResponse("basic_object_search.html", {"request": request})

@app.get("/basic_object/{id}")
async def basic_object_details(request: Request, id: str):
    return templates.TemplateResponse("basic_object_details.html", {"request": request, "id": id})


@app.get("/roles")
async def roles_page(request: Request):
    return templates.TemplateResponse("role_search.html", {"request": request})


@app.get("/roles/{role_id}")
async def role_details_page(request: Request, role_id: str):
    return templates.TemplateResponse("role_details.html", {"request": request, "role_id": role_id})


@app.get("/git_history/{module_id}")
async def git_history_page(request: Request, module_id: str):
    return templates.TemplateResponse("git_history.html", {"request": request, "module_id": module_id})