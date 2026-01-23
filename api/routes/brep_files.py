from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from uuid import UUID
from service.brep_file_service import BrepFileService
from schemas.module_version_dto import ModuleVersionDTO

router = APIRouter()

@router.post("/modules/{module_id}/brep")
async def save_brep_file_endpoint(
    module_id: str,
    file: UploadFile = File(...),
    filename: str = Form(None)
):
    try:
        module_uuid = UUID(module_id)
        actual_filename = filename or file.filename
        if not actual_filename:
            raise HTTPException(status_code=400, detail="Filename required")
        
        service = BrepFileService()
        version = service.save_single_brep_file(
            module_uuid,
            actual_filename,
            await file.read(),
            f"Add BREP file: {actual_filename}"
        )
        
        return ModuleVersionDTO.from_module_version(version)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка сохранения файла: {str(e)}")