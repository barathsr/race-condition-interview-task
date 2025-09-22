from dotenv import load_dotenv
from fastapi import FastAPI

from routers import auth, playground, redis, rooms, websocket
from utils import cors_config, openapi_config

load_dotenv()

app = FastAPI(title="Race Condition Interview Task")

cors_config.setup_cors(app)

app.include_router(playground.router)
app.include_router(websocket.router)
app.include_router(redis.router)
app.include_router(auth.router)
app.include_router(rooms.router)


@app.get("/")
def read_root():
    return {"message": "Hello!"}


openapi_config.setup_openapi(app)
