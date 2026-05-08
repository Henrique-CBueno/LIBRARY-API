

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.authors.models.author_model import AuthorModel


class AuthorRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        author: AuthorModel,
    ):
        self.db.add(author)

        await self.db.commit()

        await self.db.refresh(author)

        return author

    async def find_by_id(
        self,
        author_id: str,
    ):
        query = select(AuthorModel).where(
            AuthorModel.id == author_id
        )

        result = await self.db.execute(query)

        return result.scalar_one_or_none()