from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def setup_openapi(app: FastAPI):
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        description=(
            "Advanced FastAPI + WebSocket + Redis — "
            "Race-Condition is a horizontally scalable, "
            "WebSocket-based real-time scoreboard for "
            "coding interviews using FastAPI and Redis."
        ),
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchema"] = {
        "BearerAuth": {
            "type": "http",
            "schema": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", [{"BearerAuth": []}])
    app.openapi_schema = openapi_schema
    return app.openapi_schema
