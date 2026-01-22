from typing import Optional, Dict
from uuid import UUID
from models import BoundingContour
from . import BaseRepository


class BoundingContourRepository(BaseRepository):

    def get_by_basic_object_id(self, basic_object_id: UUID) -> Optional[BoundingContour]:
        with self.db_session.session() as db:
            return db.query(BoundingContour).filter(
                BoundingContour.basic_object_id == basic_object_id
            ).first()

    def update_brep_files(self, module_id: UUID, brep_files: Dict[str, str]) -> BoundingContour:
        with self.db_session.session() as db:
            contour = db.query(BoundingContour).filter(
                BoundingContour.basic_object_id == module_id
            ).first()
            if not contour:
                raise ValueError(f"BoundingContour for module {module_id} not found")
            if contour.brep_files is None:
                contour.brep_files = {}
            contour.brep_files.update(brep_files)
            db.commit()
            db.refresh(contour)
        return contour