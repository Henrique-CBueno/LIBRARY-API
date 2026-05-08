from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.infra.middleware.logging import LoggingMiddleware
from app.infra.middleware.request_id import RequestIDMiddleware
from app.infra.observability.logging import setup_logging
from app.exceptions.base import (
    BusinessRuleException,
    NotFoundException,
    UnauthorizedException,
)
from app.exceptions.handlers import (
    business_exception_handler,
    not_found_exception_handler,
    unauthorized_exception_handler,
)

from app.domain.users.controllers.user_controller import router as user_router

setup_logging()

app = FastAPI(title="Library Management API", version="1.0.0")

app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)

app.add_exception_handler(
    BusinessRuleException,
    business_exception_handler,
)
app.add_exception_handler(
    NotFoundException,
    not_found_exception_handler,
)
app.add_exception_handler(
    UnauthorizedException,
    unauthorized_exception_handler,
)

app.include_router(user_router)

Instrumentator().instrument(app).expose(app)


@app.get("/")
async def root():
    return {"message": "API running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
