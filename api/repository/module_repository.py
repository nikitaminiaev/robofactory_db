from uuid import UUID
from sqlalchemy.orm import joinedload
from . import BaseRepository
from models import Module


class ModuleRepository(BaseRepository):
    def get_all_basic_objects(self) -> list[Module]:
        with (self.db_session.session() as db):
            basic_objects = db.query(Module).options(
                joinedload(Module.bounding_contour),
                joinedload(Module.children),
                joinedload(Module.parents)
            ).all()
        return basic_objects

    def get_basic_object(self, name: str) -> Module:
        with self.db_session.session() as db:
            basic_object = db.query(Module).filter_by(name=name).first()
        return basic_object

    def get_basic_object_with_relations(self, name: str) -> Module:
        with self.db_session.session() as db:
            basic_object = db.query(Module).options(
                joinedload(Module.bounding_contour),
                joinedload(Module.children),
                joinedload(Module.parents)
            ).filter_by(name=name).first()
        return basic_object
    
    def get_basic_object_by_id(self, id: UUID) -> Module:
        with self.db_session.session() as db:
            basic_object = db.query(Module).filter_by(id=id).first()
        return basic_object

    def get_basic_object_for_update(self, id: UUID, db_session) -> Module:
        return db_session.query(Module).filter_by(id=id).first()

    def get_basic_object_with_relations_by_id(self, id: UUID) -> Module:
        with self.db_session.session() as db:
            basic_object = db.query(Module).options(
                joinedload(Module.bounding_contour),
                joinedload(Module.children),
                joinedload(Module.parents)
            ).filter_by(id=id).first()
        return basic_object