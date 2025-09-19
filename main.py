from fastapi import FastAPI

from routers import playground

app = FastAPI()

app.include_router(playground.router)


@app.get("/")
def read_root():
    return {"message": "Hello!"}
