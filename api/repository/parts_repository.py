from sqlalchemy import text
from .db_session import Db_session


class PartRepository:
    def __init__(self):
        self.db_session = Db_session()

    def get_row(self):
        query = "select * from parts;"

        with self.db_session.session() as db:
            result = db.execute(text(query))
        return result.fetchall()
