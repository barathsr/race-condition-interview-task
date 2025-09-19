from fastapi import FastAPI
import redis.asyncio as redis

app = FastAPI()

redis_client = redis.Redis(host="localhost", port=6379, decode_responses= True)

room_id = "OPD5"

@app.get("/")
def read_root():
    return {"message": "hello"}

@app.get("/redis-ping")
async def redisPing():
    pong = await redis_client.ping()
    return {"message": pong}

@app.post("/submit/{username}/{points}")
async def submitScore(username: str, points: int):
    new_score = await redis_client.zincrby(f"room:{room_id}:leaderboard", points, username)
    return {"username": username, "new_score": new_score}

@app.get("/leaderboard")
async def getLeaderboard():
    scores = await redis_client.zrevrange(f"room:{room_id}:leaderboard", 0, -1, withscores=True)
    leaderboard = [{"username": user, "score": int(score)} for user, score in scores ]
    return { "room_id" : room_id, "leaderboard": leaderboard }
