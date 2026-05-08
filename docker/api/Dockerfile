FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY uv.lock .

RUN pip install uv && uv sync

COPY . .

CMD ["sh", "-c", "until uv run alembic upgrade head; do sleep 2; done && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"]
