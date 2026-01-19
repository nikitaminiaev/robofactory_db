from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from uuid import UUID
from service.brep_storage import save_brep_file
from service.git_manager import commit_module_changes
from repository.module_version_repository import ModuleVersionRepository
from schemas.module_version_dto import ModuleVersionDTO
from models import Module
from sqlalchemy.orm import selectinload
from api.repository.db_session import Db_session

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
        
        # Сохранить файл
        relative_path = save_brep_file(module_uuid, actual_filename, await file.read())
        
        # Обновить bounding_contour
        db_session_factory = Db_session().session
        with db_session_factory() as db:
            module = db.query(Module).options(selectinload(Module.bounding_contour)).filter_by(id=module_uuid).first()
            if not module or not module.bounding_contour:
                raise HTTPException(status_code=404, detail="Module or bounding_contour not found")
            
            if module.bounding_contour.brep_files is None:
                module.bounding_contour.brep_files = {}
            module.bounding_contour.brep_files[actual_filename] = relative_path
            db.commit()
        
        # Коммит
        commit_hash = commit_module_changes(module_uuid, f"Add BREP file: {actual_filename}")
        
        # Создать версию
        repo = ModuleVersionRepository()
        version = repo.create_version(
            module_id=module_uuid,
            version_number="auto",
            description=f"Add BREP file: {actual_filename}",
            commit_hash=commit_hash
        )
        
        return ModuleVersionDTO.from_module_version(version)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка сохранения файла: {str(e)}")