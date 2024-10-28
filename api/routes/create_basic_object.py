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
    # Check if object exists
    existing_object = basic_repo.get_basic_object(item.name)
    if existing_object:
        raise HTTPException(
            status_code=400,
            detail="Объект с таким именем уже существует"
        )

    try:
        # Separate basic object data from bounding contour data
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