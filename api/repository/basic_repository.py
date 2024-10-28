from uuid import UUID
from sqlalchemy.orm import joinedload
from . import BaseRepository
from models import BasicObject


class BasicObjectRepository(BaseRepository):
    def get_all_basic_objects(self) -> list[BasicObject]:
        with (self.db_session.session() as db):
            basic_objects = db.query(BasicObject).options(
                joinedload(BasicObject.bounding_contour),
                joinedload(BasicObject.children),
                joinedload(BasicObject.parents)
            ).all()
        return basic_objects

    def get_basic_object(self, name: str) -> BasicObject:
        with self.db_session.session() as db:
            basic_object = db.query(BasicObject).filter_by(name=name).first()
        return basic_object

    def get_basic_object_with_relations(self, name: str) -> BasicObject:
        with self.db_session.session() as db:
            basic_object = db.query(BasicObject).options(
                joinedload(BasicObject.bounding_contour),
                joinedload(BasicObject.children),
                joinedload(BasicObject.parents)
            ).filter_by(name=name).first()
        return basic_object
    
    def get_basic_object_by_id(self, id: UUID) -> BasicObject:
        with self.db_session.session() as db:
            basic_object = db.query(BasicObject).filter_by(id=id).first()
        return basic_object
    
    def get_basic_object_with_relations_by_id(self, id: UUID) -> BasicObject:
        with self.db_session.session() as db:
            basic_object = db.query(BasicObject).options(
                joinedload(BasicObject.bounding_contour),
                joinedload(BasicObject.children),
                joinedload(BasicObject.parents)
            ).filter_by(id=id).first()
        return basic_object