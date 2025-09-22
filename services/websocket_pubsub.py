import asyncio
import json
from datetime import datetime, timezone
from typing import Dict

from fastapi import WebSocket

from services.redis_setup import redis_client

connected: Dict[str, set[WebSocket]] = {}
pubsub_tasks: Dict[str, asyncio.Task] = {}


def k_users(room_id: str) -> str:
    return f"room:{room_id}:users"


def k_event_channel(room_id: str) -> str:
    return f"room:{room_id}:events"


def k_stats(room_id: str) -> str:
    return f"room:{room_id}:stats"


def k_history(room_id: str) -> str:
    return f"room:{room_id}:history"


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def publish_room_event(room_id: str, event: dict, history_max: int = 100):
    payload = json.dumps(event)
    await redis_client.publish(k_event_channel(room_id), payload)
    await redis_client.lpush(k_history(room_id), payload)
    await redis_client.ltrim(k_history(room_id), 0, history_max - 1)
    await redis_client.hincrby(k_stats(room_id), "message_sent", 1)


async def room_pubsub_worker(room_id: str):
    channel = k_event_channel(room_id)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)
    try:
        async for message in pubsub.listen():
            if not message:
                continue
            if message.get("type") != "message":
                continue
            payload = message.get("data")
            if not payload:
                continue
            clients = list(connected.get(room_id, set()))
            for ws in clients:
                try:
                    await ws.send_text(payload)
                except Exception:
                    pass
    except asyncio.CancelledError:
        pass
    finally:
        try:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
        except Exception:
            pass
