"""
TODO: Write module desc
"""

import asyncio
import contextlib
import json
import random
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


class AppState:
    def __init__(self) -> None:
        self.log_buffer: deque[dict[str, Any]] = deque(maxlen=500)
        self.clients: set[WebSocket] = set()
        self.generator_task: asyncio.Task[Any] | None = None


def build_log_entry() -> dict[str, str]:
    severity = random.choice(["DEBUG", "INFO", "WARN", "ERROR"])
    message = random.choice(
        [
            "Connected to upstream service",
            "Heartbeat received",
            "User session refreshed",
            "Cache miss on lookup",
            "Slow response detected",
            "Retrying failed request",
            "Disk usage threshold exceeded",
            "Unhandled exception in worker",
        ]
    )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "severity": severity,
        "message": message,
    }


async def broadcast_log(app: FastAPI, log_entry: dict[str, Any]) -> None:
    disconnected: list[WebSocket] = []

    for client in app.state.shared.clients.copy():
        try:
            await client.send_text(json.dumps(log_entry))
        except Exception:
            disconnected.append(client)

    for client in disconnected:
        app.state.shared.clients.discard(client)


async def generate_logs(app: FastAPI) -> None:
    while True:
        log_entry = build_log_entry()
        app.state.shared.log_buffer.append(log_entry)
        await broadcast_log(app, log_entry)
        await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.shared = AppState()
    app.state.shared.generator_task = asyncio.create_task(generate_logs(app))

    try:
        yield
    finally:
        if app.state.shared.generator_task is not None:
            app.state.shared.generator_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await app.state.shared.generator_task


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def serve_index() -> FileResponse:
    return FileResponse("static/index.html")


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket) -> None:
    await websocket.accept()
    app.state.shared.clients.add(websocket)

    try:
        for log_entry in app.state.shared.log_buffer:
            await websocket.send_text(json.dumps(log_entry))

        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        app.state.shared.clients.discard(websocket)
    except Exception:
        app.state.shared.clients.discard(websocket)
        raise

async def main():
    config = uvicorn.Config("main:app", host="0.0.0.0", port=5000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
