import redis.asyncio as redis
from fastapi import APIRouter

router = APIRouter(
    prefix="/playground",
    tags=["Playground"],
)

redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

room_id = "OPD-5"


@router.get("/redis-ping")
async def redisPing():
    pong = await redis_client.ping()
    return {"message": pong}


@router.post("/submit/{username}/{points}")
async def submitScore(username: str, points: int):
    new_score = await redis_client.zincrby(
        f"room:{room_id}:leaderboard", points, username
    )
    return {"username": username, "new_score": new_score}


@router.get("/leaderboard")
async def getLeaderboard():
    scores = await redis_client.zrevrange(
        f"room:{room_id}:leaderboard", 0, -1, withscores=True
    )
    leaderboard = [{"username": user, "score": int(score)} for user, score in scores]
    return {"room_id": room_id, "leaderboard": leaderboard}
