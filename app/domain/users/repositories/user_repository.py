from sqlalchemy import select
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
        query = select(UserModel).where(UserModel.email == email)

        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def find_by_id(self, user_id: str):
        query = select(UserModel).where(UserModel.id == user_id)

        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def list_users(self):
        query = select(UserModel)

        result = await self.db.execute(query)

        return result.scalars().all()