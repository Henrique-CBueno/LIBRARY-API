from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from fastapi.params import Depends
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.observability.health import check_postgres, check_redis
from app.infra.database.session import get_db
from app.infra.middleware.logging import LoggingMiddleware
from app.infra.middleware.rate_limit import limiter
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
from app.domain.books.controllers.book_controller import router as book_router
from app.domain.authors.controllers.author_controller import router as author_router
from app.domain.loans.controllers.loan_controller import router as loan_router
from app.domain.notifications.controllers.notification_controller import router as notifications_router
from app.domain.reservation.controllers.reservation_controller import router as reservation_router
from app.domain.reports.controllers.report_controller import router as reports_router

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from app.schedule.scheduler import start_scheduler

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield

app = FastAPI(title="Library Management API", version="1.0.0")

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)

app.add_middleware(SlowAPIMiddleware)

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
app.include_router(author_router)
app.include_router(book_router)
app.include_router(loan_router)
app.include_router(notifications_router)
app.include_router(reservation_router)
app.include_router(reports_router)

Instrumentator().instrument(app).expose(app)


@app.get("/")
async def root():
    return {"message": "API running"}


@app.get("/health", tags=["Observability"])
async def health(
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    postgres_ok = await check_postgres(db)
    redis_ok = await check_redis()

    is_healthy = postgres_ok and redis_ok
    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "services": {
            "postgres": "healthy" if postgres_ok else "unhealthy",
            "redis": "healthy" if redis_ok else "unhealthy",
        },
    }
