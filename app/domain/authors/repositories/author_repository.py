from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

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
            AuthorModel.id == author_id,
            AuthorModel.is_active.is_(True),
        )

        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def list_authors_paginated(
        self,
        page: int,
        size: int,
    ):
        offset = (page - 1) * size

        query = (
            select(AuthorModel)
            .where(AuthorModel.is_active.is_(True))
            .order_by(AuthorModel.created_at.asc())
            .offset(offset)
            .limit(size)
        )

        result = await self.db.execute(query)

        authors = result.scalars().all()

        total_query = (
            select(func.count())
            .select_from(AuthorModel)
            .where(AuthorModel.is_active.is_(True))
        )

        total_result = await self.db.execute(
            total_query
        )

        total = total_result.scalar() or 0

        return authors, total

    async def find_by_id_with_books(
        self,
        author_id: str,
    ):
        query = (
            select(AuthorModel)
            .options(joinedload(AuthorModel.books))
            .where(
                AuthorModel.id == author_id,
                AuthorModel.is_active.is_(True),
            )
        )

        result = await self.db.execute(query)

        return result.unique().scalar_one_or_none()

    async def soft_delete(
        self,
        author: AuthorModel,
    ):
        author.is_active = False

        for book in author.books:
            if book.is_active:
                book.is_active = False

        await self.db.commit()

    async def update(
        self,
        author: AuthorModel,
    ):
        await self.db.commit()

        await self.db.refresh(author)

        return author
