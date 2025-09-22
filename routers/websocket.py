import asyncio
import json

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
    status,
)

from dependencies.auth import get_user_from_websocket
from services.websocket_pubsub import (
    connected,
    iso_now,
    k_users,
    publish_room_event,
    pubsub_tasks,
    redis_client,
    room_pubsub_worker,
)

router = APIRouter(prefix="/ws", tags=["Websocket"])


@router.get("/hi")
async def giveMeHi():
    return {"message": "hi"}


@router.websocket("/{room_id}")
async def websocket_room(websocket: WebSocket, room_id: str):
    q = websocket.query_params
    username = q.get("username")
    token = q.get("token")

    if not username or not token:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="username and token required!"
        )
        print("username and token required!")
        return

    try:
        token_username = await get_user_from_websocket(websocket, token)
    except WebSocketException:
        return

    if token_username != username:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="username mismatch with token!",
        )
        print("username mismatch with token!")
        return

    await websocket.accept()

    clients = connected.setdefault(room_id, set())
    clients.add(websocket)

    if room_id not in pubsub_tasks:
        task = asyncio.create_task(room_pubsub_worker(room_id))
        pubsub_tasks[room_id] = task

    try:
        await redis_client.sadd(k_users(room_id), username)
    except Exception:
        pass

    join_event = {
        "type": "system",
        "action": "join",
        "username": username,
        "timestamp": iso_now(),
    }
    try:
        await publish_room_event(room_id, join_event)
    except Exception:
        pass

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
                continue
            msg_type = msg.get("type")
            if msg_type == "chat":
                await redis_client.hincrby(f"room:{room_id}:stats", "messages_sent", 1)

                event = {
                    "type": "chat",
                    "username": username,
                    "message": msg.get("message", ""),
                    "timestamp": iso_now(),
                }

                await publish_room_event(room_id, event)
            elif msg_type == "submission":
                problem_id = msg.get("problem_id")
                points = int(msg.get("points", 0))

                if not problem_id or points <= 0:
                    continue

                await redis_client.hincrby(f"room:{room_id}:stats", "submissions", 1)

                new_score = await redis_client.zincrby(
                    f"room:{room_id}:leaderboard", points, username
                )

                bonus_awarded = False
                key_first = f"problem:{room_id}:{problem_id}:first_solver"
                if await redis_client.set(key_first, username, nx=True):
                    bonus_points = 10
                    new_score = await redis_client.zincrby(
                        f"room:{room_id}:leaderboard", bonus_points, username
                    )
                    bonus_awarded = True

                event = {
                    "type": "submission",
                    "username": username,
                    "problem_id": problem_id,
                    "points": points,
                    "new_score": new_score,
                    "bonus_awarded": bonus_awarded,
                    "timestamp": iso_now(),
                }
                await publish_room_event(room_id, event)

            else:
                await websocket.send_json({"error": "unknown message type"})
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        connected.get(room_id, set()).discard(websocket)
        if not connected.get(room_id):
            task = pubsub_tasks.pop(room_id, None)
            if task:
                task.cancel()

        try:
            await redis_client.srem(k_users(room_id), username)
        except Exception:
            pass

        leave_event = {
            "type": "system",
            "action": "leave",
            "username": username,
            "timestamp": iso_now(),
        }

        try:
            await publish_room_event(room_id, leave_event)
        except Exception:
            pass


@router.websocket("/leaderboard")
async def websocketEndpoint(websocket: WebSocket):
    await websocket.accept()
    room_id = "OPD-5"
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
