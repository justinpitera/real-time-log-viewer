# real-time-log-viewer

A lightweight demo app that generates fake log entries and streams them to the browser in real time over WebSockets.

A new log is produced every second. The server keeps the last 500 entries in memory, so late-joining clients receive recent history before switching to the live stream.

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, Uvicorn |
| Package manager | [uv](https://github.com/astral-sh/uv) |
| Frontend | Vanilla JS, Tailwind CSS, nginx |
| Container | Docker + Docker Compose |

## How it works

1. On startup, a background task begins emitting one log entry per second.
2. Each entry has a UTC timestamp, a level (`DEBUG` / `INFO` / `WARN` / `ERROR`), and a message.
3. Every entry is appended to an in-memory ring buffer (capacity: 500) and broadcast to all connected WebSocket clients.
4. When a client connects to `/ws/logs`, it first receives the buffered history, then continues receiving live entries.
5. The frontend is served as a static site by nginx; it connects to the backend WebSocket at `ws://localhost:8000/ws/logs`.

## Running locally with Docker Compose

**Prerequisites:** Docker and Docker Compose installed.

```bash
# Clone the repo (if you haven't already)
git clone https://github.com/your-org/real-time-log-viewer.git
cd real-time-log-viewer

# Build both images and start the services
docker-compose up --build
```

Once running, open your browser at:

| Service | URL |
|---|---|
| Frontend | http://localhost |
| Backend (WebSocket) | ws://localhost:8000/ws/logs |

Click **Connect** in the top-right corner of the UI to start receiving the live log stream.

To stop:

```bash
docker-compose down
```

## Running locally without Docker

**Prerequisites:** Python 3.12+, `uv` installed.

```bash
# Install backend dependencies
cd server
uv sync

# Start the backend
uv run uvicorn main:app --reload
```

For the frontend, serve `client/` with any static file server, for example:

```bash
cd client
python -m http.server 8080
```

Then open `http://localhost:8080`. The frontend connects to the backend at `ws://localhost:8000/ws/logs`.

## Linting

```bash
cd server
uv run ruff check .
```

Or install the pre-commit hooks to run automatically on every commit:

```bash
pip install pre-commit
pre-commit install
```

## Project structure

```
.
├── client/
│   ├── index.html     # Single-page UI
│   ├── app.js         # WebSocket client logic
│   ├── style.css      # Custom styles (Tailwind augments)
│   ├── nginx.conf     # nginx config for the static server
│   └── Dockerfile     # Builds nginx image serving the frontend
├── server/
│   ├── main.py        # FastAPI app — log generator, WebSocket endpoint
│   ├── pyproject.toml
│   ├── uv.lock
│   └── Dockerfile     # Builds the Python backend image
├── docker-compose.yml # Brings up both services together
└── .pre-commit-config.yaml
```
