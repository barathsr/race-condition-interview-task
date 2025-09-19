import json

import redis.asyncio as redis
from fastapi import APIRouter

router = APIRouter(prefix="/redis", tags=["Redis"])

room_id = "OPD-5"

redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)


@router.post("/submit/{username}/{points}")
async def submitScore(username: str, points: int):
    new_score = await redis_client.zincrby(
        f"room:{room_id}:leaderboard", points, username
    )

    scores = await redis_client.zrevrange(
        f"room:{room_id}:leaderboard", 0, -1, withscores=True
    )
    leaderboard = [{"username": user, "score": int(score)} for user, score in scores]

    update_message = json.dumps({"room_id": room_id, "leaderboard": leaderboard})
    await redis_client.publish(f"room:{room_id}:channel", update_message)
    return {"username": username, "new_score": new_score}
