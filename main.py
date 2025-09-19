from fastapi import FastAPI

from routers import playground, redis, websocket

app = FastAPI()

app.include_router(playground.router)
app.include_router(websocket.router)
app.include_router(redis.router)


@app.get("/")
def read_root():
    return {"message": "Hello!"}
