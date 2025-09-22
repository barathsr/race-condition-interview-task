from services.redis_setup import redis_client


async def get_leaderboard(room_id: str, top_n: int = 100):
    key = f"room:{room_id}:leaderboard"
    raw = await redis_client.zrevrange(key, 0, top_n - 1, withscores=True)
    return [{"username": user, "score": int(score)} for (user, score) in raw]
