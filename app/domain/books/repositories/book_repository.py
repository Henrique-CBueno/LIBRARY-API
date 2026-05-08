from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

    async def list_books(self):
        query = select(BookModel)

        result = await self.db.execute(query)

        return result.scalars().all()