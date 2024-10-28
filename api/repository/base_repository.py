from .db_session import Db_session

class BaseRepository:
    def __init__(self):
        self.db_session = Db_session()