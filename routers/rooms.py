from fastapi import APIRouter, Depends, HTTPException, status

from dependencies.auth import get_current_user
from helpers.redis import generate_room_id
from services.redis_setup import redis_client
from services.websocket_pubsub import iso_now

router = APIRouter(
    prefix="/rooms",
    tags=["Rooms"],
)


@router.get("/admin")
async def get_all_rooms_admin(user=Depends(get_current_user)):
    # if user.get("role") != "admin":
    #     raise HTTPException(status_code=403, detail="Admins only")
    room_ids = await redis_client.smembers("rooms:all")
    rooms = []

    for room_id in room_ids:
        meta = await redis_client.hgetall(f"room:{room_id}:meta")
        members = await redis_client.smembers(f"room:{room_id}:members")
        stats = await redis_client.hgetall(f"room:{room_id}:stats")
        leaderboard_raw = await redis_client.zrevrange(
            f"room:{room_id}:leaderboard", 0, -1, withscores=True
        )
        leaderboard = [
            {"username": username, "score": int(score)}
            for username, score in leaderboard_raw
        ]

        rooms.append(
            {
                "room_id": room_id,
                "meta": meta,
                "members": list(members),
                "stats": stats,
                "leaderboard": leaderboard,
            }
        )

    return {"rooms": rooms}


@router.get("/")
async def get_all_rooms(user=Depends(get_current_user)):
    username = user["username"]
    room_ids = await redis_client.smembers("rooms:all")
    print(room_ids)
    rooms = []

    for room_id in room_ids:
        members = await redis_client.smembers(f"room:{room_id}:members")
        print("Room:", room_id)
        print("Members raw:", members)
        print("Current user:", username.encode())
        if username.encode() not in members:
            continue

        meta = await redis_client.hgetall(f"room:{room_id}:meta")
        rooms.append(
            {"room_id": room_id, "meta": meta, "members": [m.decode() for m in members]}
        )

    return {"rooms": rooms}


@router.post("/create")
async def create_room(user=Depends(get_current_user)):
    room_id = await generate_room_id()
    key = f"room:{room_id}:meta"

    await redis_client.hset(
        key,
        mapping={
            "owner": user["username"],
            "created_at": iso_now(),
        },
    )

    await redis_client.sadd(f"room:{room_id}:members", user["username"])
    await redis_client.sadd("rooms:all", room_id)
    return {"room_id": room_id, "owner": user["username"]}


@router.post("/join/{room_id}")
async def join_room(room_id: str, user=Depends(get_current_user)):
    try:
        exists = await redis_client.exists(f"room:{room_id}:meta")
        if not exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Room: '{room_id}' Not found!",
            )
        await redis_client.sadd(f"room:{room_id}:members", user["username"])
        return {"message": f"{user['username']} joined room {room_id}"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete("/{room_id}")
async def delete_room(room_id: str, user=Depends(get_current_user)):
    meta = await redis_client.hgetall(f"room:{room_id}:meta")
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Room not found"
        )

    owner = meta.get(b"owner", b"").decode()
    if owner != user["username"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can delete this room",
        )

    await redis_client.delete(
        f"room:{room_id}:meta",
        f"room:{room_id}:members",
        f"room:{room_id}:leaderboard",
        f"room:{room_id}:stats",
        f"room:{room_id}:events",
        f"room:{room_id}:users",
        f"room:{room_id}:history",
    )
    await redis_client.srem("rooms:all", room_id)  # ✅ cleanup global set

    return {"message": f"Room {room_id} deleted successfully"}


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
