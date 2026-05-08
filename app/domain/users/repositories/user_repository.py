from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.users.models.user_model import UserModel


class UserRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user: UserModel):
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def find_by_email(self, email: str):
        query = select(UserModel).where(
            UserModel.email == email,
            UserModel.is_active.is_(True),
        )

        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def find_by_id(self, user_id: str):
        query = select(UserModel).where(
            UserModel.id == user_id,
            UserModel.is_active.is_(True),
        )

        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def list_users(self):
        query = select(UserModel).where(UserModel.is_active.is_(True))

        result = await self.db.execute(query)

        return result.scalars().all()

    async def list_users_paginated(
        self,
        page: int,
        size: int,
    ):
        offset = (page - 1) * size

        query = (
            select(UserModel)
            .where(UserModel.is_active.is_(True))
            .offset(offset)
            .limit(size)
        )

        result = await self.db.execute(query)

        users = result.scalars().all()

        total_query = (
            select(func.count())
            .select_from(UserModel)
            .where(UserModel.is_active.is_(True))
        )

        total_result = await self.db.execute(total_query)

        total = total_result.scalar()

        return users, total

    async def update(self, user: UserModel):
        await self.db.commit()
        await self.db.refresh(user)

        return user
