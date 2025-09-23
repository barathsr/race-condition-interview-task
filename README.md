# 🚀 Race-condition-interview-task (Real-Time Interview scoreboard)
Advanced FastAPI + WebSocket + Redis — Race-Condition is a horizontally scalable, WebSocket-based real-time scoreboard for coding interviews using FastAPI and Redis.

---

## 📌 Features
- **WebSocket endpoints** for chat, submissions, and system events  
- **Atomic Redis updates** for scores (no race conditions)  
- **First-correct bonus** per problem  
- **Live leaderboard & stats** synced across clients  
- **Room management** (create, join, leave, delete)  
- **JWT authentication** for both REST & WebSocket  

---

## ⚙️ Tech Stack
- **Python 3.10+**  
- **FastAPI** (REST + WebSocket)  
- **Redis** (Pub/Sub, ZSET leaderboard, SET membership)  
- **redis.asyncio** client  

---

## 📂 Project Structure
```
.
├── main.py                  # FastAPI entrypoint
├── routers/
│   ├── auth.py              # Auth management APIs
│   ├── playground.py        # Ignore this APIs (Just for practice)
│   ├── redis.py             # Ignore this APIs (Just for practice)
│   ├── rooms.py             # Rooms management APIs
│   ├── websocket.py         # WebSocket handling
├── services/
│   ├── redis_setup.py       # Redis client setup
│   ├── websocket_pubsub.py  # Pub/Sub helpers
├── utils/
│   ├── cors_config.py       # Configurations for CORS 
│   ├── openapi_config.py    # Configurations for swagger documentation
├── dependencies/
│   └── auth.py              # JWT auth helpers
├── helpers/
│   └── redis.py             # Utility helpers (leaderboard, ID gen)
└── README.md
```

## 🛠️ Setup Instructions
1️⃣ Clone Repo

```
> git clone https://github.com/barathsr/race-condition-interview-task.git

> cd race-condition-interview-task

```

2️⃣ Setup Virtual Environment

```
python -m venv venv

source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows
```

3️⃣ Install Dependencies

```
pip install -r requirements.txt
```
4️⃣ Run Redis

Make sure Redis is running locally. If you have Docker:
```
docker run --name redis -p 6379:6379 -d redis:latest
```

5️⃣ Environment Variables

Create a .env file:
```
SECRET_KEY=your_jwt_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REDIS_HOST=localhost
REDIS_PORT=6379
```
---
## 🚀 Running the App
Create a .env file:
```
uvicorn main:app --reload
```

Server runs at:
👉 http://127.0.0.1:8000

Swagger Docs:
👉 http://127.0.0.1:8000/docs

---
## 🔗 REST Endpoints
🏠 Rooms
- POST /rooms/create → Create room (Id will be generated automatically, owner auto-joins the room) 

- POST /rooms/join/{room_id} → Join a room

- POST /rooms/leave/{room_id} → Leave a room (ownership transfer if owner leaves)

- DELETE /rooms/{room_id} → Delete room (owner only)

📊 Leaderboard & Stats

- GET /rooms/{room_id}/leaderboard → Get live leaderboard

- GET /rooms/{room_id}/stats → Get active users & submission counters

---
## 🔌 WebSocket Endpoints
Connect 
```
ws://localhost:8000/ws/{room_id}?username=barath&token=<jwt>
```
---
## Message Schema
```
# Chat
{
  "type": "chat",
  "message": "Hello everyone!"
}

# Submission
{
  "type": "submission",
  "problem_id": "p1",
  "points": 20
}
```

### Event Types

chat → User messages

submission → Updates leaderboard (atomic)

system → Join/leave/scoreboard updates

---

## ✅ Expected Output
### Leaderboard
```
{
  "room_id": "ASRBMK",
  "leaderboard": [
    {"username": "alice", "score": 120},
    {"username": "bob", "score": 90},
    {"username": "charlie", "score": 50}
  ]
}
```
### Stats
```
{
  "room_id": "abc123",
  "active_users": 3,
  "messages_sent": 45,
  "submissions": 12
}

```

---
## 📜 License
MIT License © 2025 Barathkumar S R
 
