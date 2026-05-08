from app.config.security.hashing import hash_password, verify_password
from app.config.security.jwt import create_access_token
from app.domain.users.models.user_model import UserModel
from app.domain.users.repositories.user_repository import UserRepository
from app.domain.users.schemas.user_schema import (
    CreateUserSchema,
    LoginSchema,
    UpdateUserSchema,
)
from app.exceptions.base import BusinessRuleException, NotFoundException


class UserService:

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def create_user(
        self,
        data: CreateUserSchema,
    ):
        existing_user = await self.repository.find_by_email(str(data.email))

        if existing_user:
            raise BusinessRuleException("Email already exists")

        user = UserModel(
            name=data.name,
            email=str(data.email),
            password=hash_password(data.password),
        )

        return await self.repository.create(user)

    async def get_user(
        self,
        user_id: str,
    ):
        user = await self.repository.find_by_id(user_id)

        if not user:
            raise NotFoundException("User not found")

        return user

    async def list_users(self):
        return await self.repository.list_users()

    async def login(
        self,
        data: LoginSchema,
    ):
        user = await self.repository.find_by_email(str(data.email))

        if not user:
            raise BusinessRuleException("Invalid credentials")

        valid_password = verify_password(
            data.password,
            user.password,
        )

        if not valid_password:
            raise BusinessRuleException("Invalid credentials")

        token = create_access_token(str(user.id))

        return {"access_token": token}

    async def get_by_id(
        self,
        user_id: str,
    ):
        user = await self.repository.find_by_id(user_id)

        if not user:
            raise NotFoundException("User not found")

        return user

    async def update_user(
        self,
        user_id: str,
        data: UpdateUserSchema,
    ):
        user = await self.get_by_id(user_id)

        if data.name:
            user.name = data.name

        return await self.repository.update(user)

    async def delete_user(
        self,
        user_id: str,
    ):
        user = await self.get_by_id(user_id)

        user.is_active = False

        await self.repository.update(user)

    async def list_users_paginated(
        self,
        page: int,
        size: int,
    ):
        users, total = await self.repository.list_users_paginated(
            page,
            size,
        )

        return {
            "items": users,
            "total": total,
            "page": page,
            "size": size,
        }
