from unittest.mock import AsyncMock

import pytest

from app.domain.users.schemas.user_schema import CreateUserSchema, LoginSchema
from app.domain.users.services.user_service import UserService
from app.exceptions.base import BusinessRuleException, NotFoundException


@pytest.mark.asyncio
async def test_should_not_create_duplicate_user():

    repository = AsyncMock()

    repository.find_by_email.return_value = True

    service = UserService(repository)

    with pytest.raises(BusinessRuleException):
        await service.create_user(
            CreateUserSchema(
                name="Henrique",
                email="henrique@email.com",
                password="123456",
            )
        )


@pytest.mark.asyncio
async def test_should_raise_exception_for_invalid_login():

    repository = AsyncMock()

    repository.find_by_email.return_value = None

    service = UserService(repository)

    with pytest.raises(BusinessRuleException):
        await service.login(
            LoginSchema(
                email="henrique@email.com",
                password="123456",
            )
        )


@pytest.mark.asyncio
async def test_should_raise_not_found():

    repository = AsyncMock()

    repository.find_by_id.return_value = None

    service = UserService(repository)

    with pytest.raises(NotFoundException):
        await service.get_by_id("00000000-0000-0000-0000-000000000000")
