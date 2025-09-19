from dotenv import load_dotenv
from fastapi import FastAPI

from routers import auth, playground, redis, websocket

load_dotenv()

app = FastAPI(title="Race Condition Interview Task")


app.include_router(playground.router)
app.include_router(websocket.router)
app.include_router(redis.router)
app.include_router(auth.router)


@app.get("/")
def read_root():
    return {"message": "Hello!"}
