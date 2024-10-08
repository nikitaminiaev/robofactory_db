# from .db_session import Db_session
# from models import Part


# class PartRepository:
#     def __init__(self):
#         self.db_session = Db_session()

#     def get_all_parts(self) -> list[Part]:
#         with self.db_session.session() as db:
#             parts = db.query(Part).all()
#         return parts

#     def get_part(self, name: str) -> Part:
#         with self.db_session.session() as db:
#             part = db.query(Part).filter_by(name=name).first()
#         return part

#     def create_part(self, name: str):
#         with self.db_session.session() as db:
#             part = Part(name=name)
#             db.add(part)
#             db.commit()
