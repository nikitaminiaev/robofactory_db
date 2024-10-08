
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes import get_all_basic_objects, get_basic_object, create_basic_object


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(get_all_basic_objects.router)
app.include_router(get_basic_object.router)
app.include_router(create_basic_object.router)

@app.get("/")
def root():
    return {"message": "Welcome to the Basic Object API"}
