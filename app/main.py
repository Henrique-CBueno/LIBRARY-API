from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.infra.middleware.logging import LoggingMiddleware
from app.infra.middleware.request_id import RequestIDMiddleware
from app.infra.observability.logging import setup_logging

setup_logging()

app = FastAPI(
    title="Library Management API",
    version="1.0.0"
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)

Instrumentator().instrument(app).expose(app)


@app.get("/")
async def root():
    return {"message": "API running"}


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }