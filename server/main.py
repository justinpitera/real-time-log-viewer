"""
A simple server that generates fake logs and streams them to the browser in real time.

It creates a new log every second, keeps the last 500 logs in memory, and sends them
to all connected Websocket clients. When someone connects, they first receive the
existing logs, then continue getting new ones live.

Built as a light weight demo.
"""

import asyncio
import contextlib
import json
import random
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect


class LogViewerState:
    def __init__(self) -> None:
        self.log_buffer: deque[dict[str, Any]] = deque(maxlen=500)
        self.clients: set[WebSocket] = set()
        self.generator_task: asyncio.Task[Any] | None = None


def build_log_entry() -> dict[str, str]:
    level = random.choice(["DEBUG", "INFO", "WARN", "ERROR"])
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
        "level": level,
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
    app.state.shared = LogViewerState()
    app.state.shared.generator_task = asyncio.create_task(generate_logs(app))

    try:
        yield
    finally:
        if app.state.shared.generator_task is not None:
            app.state.shared.generator_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await app.state.shared.generator_task


app = FastAPI(lifespan=lifespan)


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
