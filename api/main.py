from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from routes import get_all_basic_objects, get_basic_object, create_basic_object, load_freecad
import threading
from service.web_soket_server import start_server

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(get_all_basic_objects.router)
app.include_router(get_basic_object.router)
app.include_router(create_basic_object.router)
app.include_router(load_freecad.router)

# Запуск WebSocket-сервера в отдельном потоке
websocket_thread = threading.Thread(target=start_server)
websocket_thread.daemon = True
websocket_thread.start()

@app.get("/")
def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/basic_object")
async def root(request: Request):
    return templates.TemplateResponse("basic_object_search.html", {"request": request})

@app.get("/basic_object/{id}")
async def basic_object_details(request: Request, id: str):
    return templates.TemplateResponse("basic_object_details.html", {"request": request, "id": id})

@app.get("/websocket_test")
async def websocket_test(request: Request):
    return templates.TemplateResponse("websocket_test.html", {"request": request})