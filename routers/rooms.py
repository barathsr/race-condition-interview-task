from fastapi import APIRouter, HTTPException, status

from services.redis_setup import redis_client

router = APIRouter(
    prefix="/rooms",
    tags=["Rooms"],
)


@router.get("/{room_id}/leaderboard")
async def get_leaderboard(room_id: str):
    try:
        scores = await redis_client.zrevrange(
            f"room:{room_id}:leaderboard", 0, -1, withscores=True
        )
        leaderboard = [
            {"username": user, "score": int(score)} for user, score in scores
        ]

        return {"room_id": room_id, "leaderboard": leaderboard}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{room_id}/stats")
async def get_score(room_id: str):
    try:
        stats = await redis_client.hgetall(f"room:{room_id}:stats")

        stats = {k: int(v) for k, v in stats.items()}

        active_users = await redis_client.scard(f"room:{room_id}:users")

        return {
            "room_id": room_id,
            "active_users": active_users,
            **stats,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
