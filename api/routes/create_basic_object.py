import uuid as uuid_mod
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel
from repository.module_repository import ModuleRepository
from repository.role_repository import RoleRepository
from typing import Optional, Dict, List
from models import BoundingContour, Module
from uuid import UUID
import logging
from models.associations import parent_child_module
from models.module import ModuleStatus
from service.brep_file_service import BrepFileService
from service.constants import get_module_resource_path, get_module_stl_directory, build_brep_relative_path, build_stl_relative_path
from service.git_manager import commit_module_changes, init_module_git_repo, is_module_git_repo_initialized
from repository.bounding_contour_repository import BoundingContourRepository

router = APIRouter()

# Настраиваем логгер
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Создаем обработчик для вывода в консоль
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Создаем форматтер для логов
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Добавляем обработчик к логгеру
logger.addHandler(console_handler)


_EXTENSION_SUBDIR: Dict[str, Optional[str]] = {
    ".brep": "brep_files",
    ".stl": "stl_files",
    ".scad": None,  # root of module directory
}

ALLOWED_EXTENSIONS = set(_EXTENSION_SUBDIR.keys())


async def _save_uploaded_files(module_id: UUID, files: List[UploadFile]) -> Dict[str, str]:
    """
    Saves uploaded files to appropriate subdirectories based on extension.
    Returns dict of saved brep files {filename: relative_path} for BoundingContour.
    """
    repo_path = get_module_resource_path(module_id)
    brep_saved: Dict[str, str] = {}

    for upload in files:
        filename = upload.filename or ""
        ext = Path(filename).suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        subdir = _EXTENSION_SUBDIR[ext]
        target_dir = repo_path / subdir if subdir else repo_path
        target_dir.mkdir(parents=True, exist_ok=True)

        content = await upload.read()
        (target_dir / filename).write_bytes(content)

        if ext == ".brep":
            brep_saved[filename] = build_brep_relative_path(module_id, filename)

    return brep_saved


class BasicObjectCreate(BaseModel):
    name: str
    author: Optional[str] = None
    description: Optional[str] = None
    coordinates: Optional[Dict] = None
    role: Optional[str] = None
    role_description: Optional[str] = None
    is_assembly: bool = False
    is_shell: bool = False
    brep_files: Optional[Dict[str, str]] = None
    parent_id: Optional[str] = None
    status: Optional[ModuleStatus] = None


async def _create_module_in_db(
    name: str,
    author: Optional[str],
    description: Optional[str],
    is_assembly: bool,
    is_shell: bool,
    status: Optional[ModuleStatus],
    parent_id: Optional[str],
    coordinates: Optional[Dict],
    role: Optional[str],
    role_description: Optional[str],
    basic_repo: ModuleRepository,
    role_repo: RoleRepository,
) -> UUID:
    basic_object_data = {
        "name": name,
        "author": author or "unknown",
        "description": description,
        "status": status or ModuleStatus.SKETCH,
    }
    contour_data = {"is_assembly": is_assembly, "is_shell": is_shell, "brep_files": {}}

    with basic_repo.db_session.session() as db:
        basic_object = Module.create(**basic_object_data)
        db.add(basic_object)
        db.flush()
        logger.info(f"parent_id: {parent_id}, coordinates: {coordinates}")

        if parent_id and coordinates:
            parent_module = db.query(Module).filter(Module.id == parent_id).first()
            if not parent_module:
                raise HTTPException(
                    status_code=404,
                    detail=f"Родительский модуль с ID {parent_id} не найден"
                )

            role_id = None
            if role:
                role_obj = role_repo.get_or_create_role(db, role, role_description)
                role_id = role_obj.id

            db.execute(
                parent_child_module.insert().values(
                    id=uuid_mod.uuid4(),
                    parent_id=parent_id,
                    child_id=basic_object.id,
                    coordinates=coordinates,
                    role_id=role_id,
                )
            )

        contour_data["module_id"] = basic_object.id
        contour = BoundingContour.create(**contour_data)
        contour.module_id = basic_object.id
        db.add(contour)

        db.commit()
        db.refresh(basic_object)
        return basic_object.id


@router.post("/api/basic_object/")
async def create_basic_object(
        item: BasicObjectCreate,
        basic_repo: ModuleRepository = Depends(),
        role_repo: RoleRepository = Depends()
):
    """JSON endpoint — used by FreeCAD client."""
    try:
        module_id = await _create_module_in_db(
            name=item.name,
            author=item.author,
            description=item.description,
            is_assembly=item.is_assembly,
            is_shell=item.is_shell,
            status=item.status,
            parent_id=item.parent_id,
            coordinates=item.coordinates,
            role=item.role,
            role_description=item.role_description,
            basic_repo=basic_repo,
            role_repo=role_repo,
        )

        if not is_module_git_repo_initialized(module_id):
            init_module_git_repo(module_id)

        if item.brep_files:
            service = BrepFileService()
            service.save_brep_files_from_dict(
                module_id,
                item.brep_files,
                f"Initial BREP files for {item.name}"
            )

        return {"ok": True, "id": str(module_id)}

    except Exception as e:
        logger.error(f"Ошибка при создании объекта: {str(e)}", exc_info=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Ошибка при создании объекта: {str(e)}")


@router.post("/api/basic_object/form")
async def create_basic_object_form(
        name: str = Form(...),
        author: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        is_assembly: bool = Form(False),
        is_shell: bool = Form(False),
        parent_id: Optional[str] = Form(None),
        status: Optional[str] = Form(None),
        files: Optional[List[UploadFile]] = File(None),
        basic_repo: ModuleRepository = Depends(),
        role_repo: RoleRepository = Depends()
):
    """Multipart/form-data endpoint — used by the web UI."""
    try:
        parsed_status = ModuleStatus(status) if status else ModuleStatus.SKETCH

        module_id = await _create_module_in_db(
            name=name,
            author=author,
            description=description,
            is_assembly=is_assembly,
            is_shell=is_shell,
            status=parsed_status,
            parent_id=parent_id,
            coordinates=None,
            role=None,
            role_description=None,
            basic_repo=basic_repo,
            role_repo=role_repo,
        )

        if not is_module_git_repo_initialized(module_id):
            init_module_git_repo(module_id)

        non_empty_files = [f for f in (files or []) if f.filename]
        if non_empty_files:
            brep_saved = await _save_uploaded_files(module_id, non_empty_files)
            commit_module_changes(module_id, f"Add initial files for {name}")

            if brep_saved:
                BoundingContourRepository().update_brep_files(module_id, brep_saved)

        return {"ok": True, "id": str(module_id)}

    except Exception as e:
        logger.error(f"Ошибка при создании объекта (form): {str(e)}", exc_info=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Ошибка при создании объекта: {str(e)}")


class ChildRelation(BaseModel):
    id: str
    coordinates: Optional[Dict] = None
    role: Optional[str] = None
    role_description: Optional[str] = None


class BasicObjectUpdate(BaseModel):
    name: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    coordinates: Optional[Dict] = None
    role: Optional[str] = None
    role_description: Optional[str] = None
    is_assembly: Optional[bool] = None
    is_shell: Optional[bool] = None
    brep_files: Optional[Dict[str, str]] = None
    parent_id: Optional[str] = None
    added_children: Optional[List[ChildRelation]] = None
    removed_children: Optional[List[str]] = None
    removed_child_relations: Optional[List[str]] = None
    added_parents: Optional[List[ChildRelation]] = None
    removed_parents: Optional[List[str]] = None


@router.patch("/api/basic_object/{object_id}", status_code=200)
async def update_basic_object(
        object_id: str,
        item: BasicObjectUpdate,
        basic_repo: ModuleRepository = Depends(),
        role_repo: RoleRepository = Depends()
):
    try:
        obj_id_uuid = UUID(object_id)
        with basic_repo.db_session.session() as db:
            basic_object = basic_repo.get_module_for_update(obj_id_uuid, db)
            if not basic_object:
                raise HTTPException(
                    status_code=404,
                    detail="Объект не найден"
                )

            update_data = item.dict(exclude_unset=True)

            # 1. Обработка удаления детей
            removed_children = update_data.pop("removed_children", None)
            if removed_children:
                removed_uuids = [UUID(cid) for cid in removed_children]
                basic_repo.remove_children(obj_id_uuid, removed_uuids, db)

            # 1b. Обработка удаления конкретных связей (по parent_child_module_id)
            removed_child_relations = update_data.pop("removed_child_relations", None)
            if removed_child_relations:
                removed_rel_uuids = [UUID(rid) for rid in removed_child_relations]
                basic_repo.remove_child_relations(obj_id_uuid, removed_rel_uuids, db)

            # 2. Обработка добавления детей
            added_children = update_data.pop("added_children", None)
            if added_children:
                for child in added_children:
                    # Получаем или создаем роль для ребенка
                    child_role_id = None
                    if child.get("role"):
                        role_obj = role_repo.get_or_create_role(db, child["role"], child.get("role_description"))
                        child_role_id = role_obj.id

                    basic_repo.add_child_relation(
                        parent_id=obj_id_uuid,
                        child_id=UUID(child["id"]),
                        coordinates=child.get("coordinates"),
                        role_id=child_role_id,
                        db_session=db
                    )

            # 3. Обработка удаления родителей
            removed_parents = update_data.pop("removed_parents", None)
            if removed_parents:
                removed_parent_uuids = [UUID(pid) for pid in removed_parents]
                basic_repo.remove_parents(obj_id_uuid, removed_parent_uuids, db)

            # 4. Обработка добавления родителей
            added_parents = update_data.pop("added_parents", None)
            if added_parents:
                for parent in added_parents:
                    # Получаем или создаем роль для родителя
                    parent_role_id = None
                    if parent.get("role"):
                        role_obj = role_repo.get_or_create_role(db, parent["role"], parent.get("role_description"))
                        parent_role_id = role_obj.id

                    basic_repo.add_parent_relation(
                        child_id=obj_id_uuid,
                        parent_id=UUID(parent["id"]),
                        coordinates=parent.get("coordinates"),
                        role_id=parent_role_id,
                        db_session=db
                    )

            # Обновляем связь в parent_child_module если есть parent_id или coordinates (связь ТЕКУЩЕГО объекта с его родителем)
            if "parent_id" in update_data or "coordinates" in update_data or "role" in update_data:
                # Получаем текущие данные
                current_relation = db.query(parent_child_module).filter(
                    parent_child_module.c.child_id == obj_id_uuid
                ).first()

                new_parent_id = update_data.get("parent_id")
                new_parent_uuid = UUID(new_parent_id) if new_parent_id else None
                new_coordinates = update_data.get("coordinates")
                new_role = update_data.get("role")
                new_role_description = update_data.get("role_description")

                # Обрабатываем роль
                role_id = None
                if new_role:
                    role = role_repo.get_or_create_role(db, new_role, new_role_description)
                    role_id = role.id
                    if role.description != new_role_description:
                        role.description = new_role_description
                        db.commit()
                        db.refresh(role)

                if current_relation:    
                    # Обновляем существующую запись
                    if new_parent_uuid or new_coordinates or role_id:
                        update_values = {}
                        if new_parent_uuid:
                            update_values["parent_id"] = new_parent_uuid
                        if new_coordinates:
                            update_values["coordinates"] = new_coordinates
                        if role_id:
                            update_values["role_id"] = role_id
                        db.execute(
                            parent_child_module.update()
                            .where(parent_child_module.c.child_id == obj_id_uuid)
                            .values(**update_values)
                        )
                elif new_parent_uuid and new_coordinates:
                    db.execute(
                        parent_child_module.insert().values(
                            id=uuid_mod.uuid4(),
                            parent_id=new_parent_uuid,
                            child_id=obj_id_uuid,
                            coordinates=new_coordinates,
                            role_id=role_id,
                        )
                    )

            # Удаляем поля, которые обрабатываются отдельно
            for field in ["parent_id", "coordinates", "role", "role_description"]:
                update_data.pop(field, None)

            contour_fields = {"is_assembly", "is_shell", "brep_files"}
            basic_object_data = {k: v for k, v in update_data.items() if k not in contour_fields}
            contour_data = {k: v for k, v in update_data.items() if k in contour_fields}

            for field, value in basic_object_data.items():
                setattr(basic_object, field, value)

            # Обновляем поля контура
            if contour_data:
                contour = basic_object.bounding_contour
                if contour:
                    for field, value in contour_data.items():
                        if field == "brep_files":
                            if value:
                                service = BrepFileService()
                                service.save_brep_files_from_dict(
                                    obj_id_uuid,
                                    value,
                                    f"Update BREP files for {basic_object.name}"
                                )
                        else:
                            setattr(contour, field, value)

            db.commit()
            db.refresh(basic_object)

            return {"ok": True, "id": str(basic_object.id)}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обновлении объекта: {str(e)}"
        )


class ParentChildModuleUpdate(BaseModel):
    coordinates: Optional[Dict] = None


@router.patch("/api/parent_child_module/{record_id}", status_code=200)
async def update_parent_child_module_record(
        record_id: str,
        item: ParentChildModuleUpdate,
        basic_repo: ModuleRepository = Depends()
):
    """
    Обновляет конкретную запись в parent_child_module по её ID.
    Используется для сохранения координат конкретного экземпляра дочернего объекта в сборке.
    """
    try:
        record_uuid = UUID(record_id)
        with basic_repo.db_session.session() as db:
            stmt = (
                parent_child_module.update()
                .where(parent_child_module.c.id == record_uuid)
                .values(coordinates=item.coordinates)
            )
            result = db.execute(stmt)
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"Запись в parent_child_module с ID '{record_id}' не найдена"
                )
            db.commit()
            return {"ok": True, "id": str(record_uuid)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обновлении записи: {str(e)}"
        )