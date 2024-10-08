from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from repository.basic_repository import BasicObjectRepository

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/basic_object")
def get_basic_object(request: Request, name: str = None, repo: BasicObjectRepository = Depends()):
    error_message = None
    basic_object = None
    
    if name:
        basic_object = repo.get_basic_object(name)
        if not basic_object:
            error_message = f"Объект с именем '{name}' не найден"
    
    return templates.TemplateResponse("basic_object_search.html", {
        "request": request,
        "basic_object": basic_object,
        "error_message": error_message,
        "search_performed": name is not None
    })