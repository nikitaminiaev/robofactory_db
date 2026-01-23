from typing import Optional, Dict
from uuid import UUID
from models import BoundingContour
from . import BaseRepository


class BoundingContourRepository(BaseRepository):

    def get_by_module_id(self, module_id: UUID) -> Optional[BoundingContour]:
        with self.db_session.session() as db:
            return db.query(BoundingContour).filter(
                BoundingContour.module_id == module_id
            ).first()

    def update_brep_files(self, module_id: UUID, brep_files: Dict[str, str]) -> BoundingContour:
        with self.db_session.session() as db:
            contour = db.query(BoundingContour).filter(
                BoundingContour.module_id == module_id
            ).first()
            if not contour:
                raise ValueError(f"BoundingContour for module {module_id} not found")
            current_files = contour.brep_files or {}
            contour.brep_files = {**current_files, **brep_files}

            db.add(contour)
            db.flush()
            db.commit()

            return contour
        return contour