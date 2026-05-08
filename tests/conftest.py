import asyncio

import pytest
import uuid6 as uuid
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config.security.hashing import hash_password
from app.config.security.jwt import create_access_token
from app.domain.users.enums.user_role import UserRole
from app.domain.users.models.user_model import UserModel
# Ensure all models are registered on Base.metadata for test schema setup.
from app.domain.users.models import user_model  # noqa: F401
from app.domain.books.models import book_model  # noqa: F401
from app.domain.authors.models import author_model  # noqa: F401
from app.domain.loans.models import loan_model  # noqa: F401
from app.domain.reservation.models import reservation_model  # noqa: F401
from app.domain.notifications.models import notification_model  # noqa: F401
from app.infra.database.Base import Base
from app.infra.database.session import get_db
from app.infra.middleware.rate_limit import limiter
from app.main import app

DATABASE_URL = "postgresql+asyncpg://admin:admin@localhost:5433/library_test"

engine = create_async_engine(
    DATABASE_URL,
    future=True,
    poolclass=NullPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()

    yield loop

    loop.close()


@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            if session.in_transaction():
                await session.rollback()


@pytest.fixture
async def client(db_session):

    async def override_get_db():
        yield db_session

    admin = UserModel(
        name="Test Admin",
        email=f"{uuid.uuid7()}@email.com",
        password=hash_password("123456"),
        is_active=True,
        role=UserRole.ADMIN.value,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    token = create_access_token(str(admin.id), admin.role)

    limiter.enabled = False
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
    limiter.enabled = True


@pytest.fixture
async def anonymous_client(db_session):

    async def override_get_db():
        yield db_session

    limiter.enabled = False
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
    limiter.enabled = True
