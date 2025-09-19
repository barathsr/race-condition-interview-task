import json

import redis.asyncio as redis
from fastapi import APIRouter, WebSocket

router = APIRouter(prefix="/ws", tags=["Websocket"])

redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

room_id = "OPD-5"


@router.get("/hi")
async def giveMeHi():
    return {"message": "hi"}


@router.websocket("/leaderboard")
async def websocketEndpoint(websocket: WebSocket):
    await websocket.accept()

    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"room:{room_id}:channel")

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await websocket.send_json(data)

    finally:
        await pubsub.unsubscribe(f"room:{room_id}:channel")
        await pubsub.close()
