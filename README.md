# real-time-log-viewer

A lightweight demo app that generates fake log entries and streams them to the browser in real time over WebSockets.

A new log is produced every second. The server keeps the last 500 entries in memory, so late-joining clients receive recent history before switching to the live stream.

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, Uvicorn |
| Package manager | [uv](https://github.com/astral-sh/uv) |
| Frontend | Vanilla JS, Tailwind CSS |
| Container | Docker + Docker Compose |

## How it works

1. On startup, a background task begins emitting one log entry per second.
2. Each entry has a UTC timestamp, a level (`DEBUG` / `INFO` / `WARN` / `ERROR`), and a message.
3. Every entry is appended to an in-memory ring buffer (capacity: 500) and broadcast to all connected WebSocket clients.
4. When a client connects to `/ws/logs`, it first receives the buffered history, then continues receiving live entries.

## Running locally with Docker Compose

**Prerequisites:** Docker and Docker Compose installed.

```bash
# Clone the repo (if you haven't already)
git clone https://github.com/your-org/real-time-log-viewer.git
cd real-time-log-viewer

# Build the image and start the service
docker-compose up --build
```

Once the container is running, open your browser at:

```
http://localhost:8000
```

Click **Connect** in the top-right corner of the UI to start receiving the live log stream.

To stop the service:

```bash
docker-compose down
```

## Running locally without Docker

**Prerequisites:** Python 3.12+, `uv` installed.

```bash
# Install dependencies
uv sync

# Start the development server
uv run uvicorn main:app --reload
```

Then open `http://localhost:8000`.

## Project structure

```
.
├── main.py            # FastAPI app — log generator, WebSocket endpoint
├── static/
│   ├── index.html     # Single-page UI
│   ├── app.js         # WebSocket client logic
│   └── style.css      # Custom styles (Tailwind augments)
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```
