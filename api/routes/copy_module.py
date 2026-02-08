from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import UUID
from service.module_copier import copy_module_with_roles
from schemas.basic_object_dto import BasicObjectDTO

router = APIRouter()

class CopyModuleRequest(BaseModel):
    new_author: str
    version_number: str
    description: str


@router.post("/modules/{module_id}/copy")
async def copy_module(
    module_id: str,
    request: CopyModuleRequest
):
    try:
        module_uuid = UUID(module_id)
        new_module = copy_module_with_roles(
            module_id=module_uuid,
            new_author=request.new_author,
            version_number=request.version_number,
            description=request.description
        )
        return BasicObjectDTO.from_module(new_module)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка копирования: {str(e)}")