from sqlalchemy import String, Integer, Column
from .base import Base


class Part(Base):
    __tablename__ = "parts"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)

    def __repr__(self) -> str:
        return str(self)

    def __str__(self):
        return f"Part(id={self.id!r}, name={self.name!r})"
