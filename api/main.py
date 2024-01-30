from repository.parts_repository import PartRepository
from fastapi import FastAPI
from pydantic import BaseModel


class Item(BaseModel):
    name: str


app = FastAPI()


@app.get("/parts")
def get_all():
    repo = PartRepository()
    return repo.get_all_parts()

@app.get("/part")
def get_part(name: str):
    repo = PartRepository()
    return repo.get_part(name)

@app.post("/part/")
def create_part(item: Item):
    repo = PartRepository()
    return repo.create_part(item.name)


@app.get("/")
def m():
    return "hello"
