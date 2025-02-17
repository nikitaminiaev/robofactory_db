from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from repository.basic_repository import BasicObjectRepository
from typing import Optional, Dict
from models import BoundingContour, BasicObject

router = APIRouter()


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


@router.post("/api/basic_object/")
def create_basic_object(
        item: BasicObjectCreate,
        basic_repo: BasicObjectRepository = Depends()
):
    existing_object = basic_repo.get_basic_object(item.name)
    if existing_object:
        raise HTTPException(
            status_code=400,
            detail="Объект с таким именем уже существует"
        )

    try:
        basic_object_data = {
            "name": item.name,
            "author": item.author,
            "description": item.description,
            "coordinates": item.coordinates,
            "role": item.role,
            "role_description": item.role_description
        }

        # Prepare bounding contour data
        contour_data = {
            "is_assembly": item.is_assembly,
            "brep_files": item.brep_files,
            "parent_id": item.parent_id
        }

        # Execute all operations in one session
        with basic_repo.db_session.session() as db:
            basic_object = BasicObject.create(**basic_object_data)
            # Add basic object
            db.add(basic_object)
            db.flush()  # Get basic object ID

            # Set basic object ID for contour
            contour = BoundingContour.create(**contour_data)

            contour.basic_object_id = basic_object.id
            db.add(contour)

            # Commit all changes
            db.commit()
            db.refresh(basic_object)


        return {"ok": True, "id": str(basic_object.id)}

    except Exception as e:
        # Session automatically rolls back on exception
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
        basic_repo: BasicObjectRepository = Depends()
):
    try:
        with basic_repo.db_session.session() as db:
            basic_object = basic_repo.get_basic_object_for_update(object_id, db)
            if not basic_object:
                raise HTTPException(
                    status_code=404,
                    detail="Объект не найден"
                )

            update_data = item.dict(exclude_unset=True)

            contour_fields = {"is_assembly", "brep_files", "parent_id"}
            basic_object_data = {k: v for k, v in update_data.items() if k not in contour_fields}
            contour_data = {k: v for k, v in update_data.items() if k in contour_fields}

            for field, value in basic_object_data.items():
                setattr(basic_object, field, value)

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