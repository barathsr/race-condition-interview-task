import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Dict

import redis.asyncio as redis
from fastapi import WebSocket

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

connected: Dict[str, set[WebSocket]] = {}
pubsub_tasks: Dict[str, asyncio.Task] = {}


def k_users(room_id: str) -> str:
    return f"room:{room_id}:users"


def k_event_channel(room_id: str) -> str:
    return f"room:{room_id}:events"


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def publish_room_event(room_id: str, event: dict):
    await redis_client.publish(k_event_channel(room_id), json.dumps(event))


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
