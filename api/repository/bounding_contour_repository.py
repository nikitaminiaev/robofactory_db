from typing import Optional
from uuid import UUID
from models import BoundingContour
from . import BaseRepository


class BoundingContourRepository(BaseRepository):

    def get_by_basic_object_id(self, basic_object_id: UUID) -> Optional[BoundingContour]:
        with self.db_session.session() as db:
            return db.query(BoundingContour).filter(
                BoundingContour.basic_object_id == basic_object_id
            ).first()