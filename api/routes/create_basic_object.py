from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from repository.module_repository import ModuleRepository
from repository.role_repository import RoleRepository
from typing import Optional, Dict
from models import BoundingContour, Module
import logging
from models.associations import parent_child_module
from models.module import ModuleStatus

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


class BasicObjectCreate(BaseModel):
    name: str
    author: str
    description: Optional[str] = None
    coordinates: Optional[Dict] = None
    role: Optional[str] = None
    role_description: Optional[str] = None
    is_assembly: bool
    brep_files: Dict[str, str]
    parent_id: Optional[str] = None
    status: Optional[ModuleStatus] = None


@router.post("/api/basic_object/")
def create_basic_object(
        item: BasicObjectCreate,
        basic_repo: ModuleRepository = Depends(),
        role_repo: RoleRepository = Depends()
):
    try:
        basic_object_data = {
            "name": item.name,
            "author": item.author,
            "description": item.description,
            "status": item.status if item.status else ModuleStatus.SKETCH
        }

        # Prepare bounding contour data
        contour_data = {
            "is_assembly": item.is_assembly,
            "brep_files": item.brep_files,
            # Удалено: "parent_id": item.parent_id, тут нужно искать родительский контур по bounding_contours.id
        }

        # Execute all operations in one session
        with basic_repo.db_session.session() as db:
            basic_object = Module.create(**basic_object_data)
            db.add(basic_object)
            db.flush()
            logger.info(f"parent_id: {item.parent_id}, coordinates: {item.coordinates}")

            # Если есть parent_id и coordinates, проверяем существование родителя и создаем связь
            if item.parent_id and item.coordinates:
                # Проверяем существование родительского модуля
                parent_module = db.query(Module).filter(Module.id == item.parent_id).first()
                if not parent_module:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Родительский модуль с ID {item.parent_id} не найден"
                    )
                
                # Получаем или создаем роль
                role_id = None
                if item.role:
                    role = role_repo.get_or_create_role(db, item.role, item.role_description)
                    role_id = role.id

                parent_child = parent_child_module.insert().values(
                    parent_id=item.parent_id,
                    child_id=basic_object.id,
                    coordinates=item.coordinates,
                    role_id=role_id
                )
                db.execute(parent_child)

            # Set basic object ID for contour
            contour_data["module_id"] = basic_object.id
            contour = BoundingContour.create(**contour_data)

            contour.basic_object_id = basic_object.id
            db.add(contour)

            db.commit()
            db.refresh(basic_object)

        return {"ok": True, "id": str(basic_object.id)}

    except Exception as e:
        logger.error(f"Ошибка при создании объекта: {str(e)}", exc_info=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при создании объекта: {str(e)}"
        )


class BasicObjectUpdate(BaseModel):
    name: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    coordinates: Optional[Dict] = None
    role: Optional[str] = None
    role_description: Optional[str] = None
    is_assembly: Optional[bool] = None
    brep_files: Optional[Dict[str, str]] = None
    parent_id: Optional[str] = None


@router.patch("/api/basic_object/{object_id}", status_code=200)
def update_basic_object(
        object_id: str,
        item: BasicObjectUpdate,
        basic_repo: ModuleRepository = Depends(),
        role_repo: RoleRepository = Depends()
):
    try:
        with basic_repo.db_session.session() as db:
            basic_object = basic_repo.get_module_for_update(object_id, db)
            if not basic_object:
                raise HTTPException(
                    status_code=404,
                    detail="Объект не найден"
                )

            update_data = item.dict(exclude_unset=True)

            # Обновляем связь в parent_child_module если есть parent_id или coordinates
            if "parent_id" in update_data or "coordinates" in update_data or "role" in update_data:
                # Получаем текущие данные
                current_relation = db.query(parent_child_module).filter(
                    parent_child_module.c.child_id == object_id
                ).first()

                new_parent_id = update_data.get("parent_id")
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
                    if new_parent_id or new_coordinates or role_id:
                        update_values = {}
                        if new_parent_id:
                            update_values["parent_id"] = new_parent_id
                        if new_coordinates:
                            update_values["coordinates"] = new_coordinates
                        if role_id:
                            update_values["role_id"] = role_id
                        db.execute(
                            parent_child_module.update()
                            .where(parent_child_module.c.child_id == object_id)
                            .values(**update_values)
                        )
                elif new_parent_id and new_coordinates:
                    # Создаем новую запись
                    db.execute(
                        parent_child_module.insert().values(
                            parent_id=new_parent_id,
                            child_id=object_id,
                            coordinates=new_coordinates,
                            role_id=role_id
                        )
                    )

            # Удаляем поля, которые обрабатываются отдельно
            for field in ["parent_id", "coordinates", "role", "role_description"]:
                update_data.pop(field, None)

            contour_fields = {"is_assembly", "brep_files"}
            basic_object_data = {k: v for k, v in update_data.items() if k not in contour_fields}
            contour_data = {k: v for k, v in update_data.items() if k in contour_fields}

            for field, value in basic_object_data.items():
                setattr(basic_object, field, value)

            # Обновляем поля контура
            if contour_data:
                contour = basic_object.bounding_contour
                if contour:
                    for field, value in contour_data.items():
                        setattr(contour, field, value)

            db.commit()
            db.refresh(basic_object)

            return {"ok": True, "id": str(basic_object.id)}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обновлении объекта: {str(e)}"
        )