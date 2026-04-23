FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml .
RUN uv sync --no-dev

COPY main.py .
COPY static/ static/

EXPOSE 5000

CMD ["uv", "run", "main.py"]
