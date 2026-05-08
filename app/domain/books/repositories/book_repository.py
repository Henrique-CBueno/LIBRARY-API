from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.books.models.book_model import BookModel


class BookRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        book: BookModel,
    ):
        self.db.add(book)

        await self.db.commit()

        await self.db.refresh(book)

        return book

    async def find_by_isbn(
        self,
        isbn: str,
    ):
        query = select(BookModel).where(
            BookModel.isbn == isbn
        )

        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def list_books(
            self,
            title: str | None = None,
            category: str | None = None,
    ):
        query = (
            select(BookModel)
            .options(
                joinedload(BookModel.author)
            )
        )

        if title:
            query = query.where(
                BookModel.title.ilike(f"%{title}%")
            )

        if category:
            query = query.where(
                BookModel.category == category
            )

        result = await self.db.execute(query)

        return result.scalars().all()

    async def find_by_id(
            self,
            book_id,
    ):
        query = (
            select(BookModel)
            .options(
                joinedload(BookModel.author)
            )
            .where(BookModel.id == book_id)
        )

        result = await self.db.execute(query)

        return result.scalar_one_or_none()