from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.authors.models.author_model import AuthorModel
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

    async def list_books_paginated(
            self,
            page: int,
            size: int,
            title: str | None = None,
            category: str | None = None,
            author: str | None = None,
            available: bool | None = None,
    ):
        offset = (page - 1) * size

        filters = []

        query = (
            select(BookModel)
            .options(
                joinedload(BookModel.author)
            )
            .where(
                BookModel.is_active.is_(True),
                BookModel.author.has(
                    AuthorModel.is_active.is_(True)
                ),
            )
        )

        if title:
            filters.append(
                BookModel.title.ilike(
                    f"%{title}%"
                )
            )

        if category:
            filters.append(
                BookModel.category == category
            )

        if author:
            filters.append(
                BookModel.author.has(
                    AuthorModel.name.ilike(
                        f"%{author}%"
                    )
                )
            )

        if available is not None:
            if available:
                filters.append(
                    BookModel.available_copies > 0
                )
            else:
                filters.append(
                    BookModel.available_copies == 0
                )

        if filters:
            query = query.where(*filters)

        paginated_query = (
            query
            .offset(offset)
            .limit(size)
        )

        result = await self.db.execute(
            paginated_query
        )

        books = result.scalars().all()

        total_query = (
            select(func.count())
            .select_from(BookModel)
            .where(
                BookModel.is_active.is_(True),
                BookModel.author.has(
                    AuthorModel.is_active.is_(True)
                ),
            )
        )

        if filters:
            total_query = total_query.where(
                *filters
            )

        total_result = await self.db.execute(
            total_query
        )

        total = total_result.scalar()

        return books, total

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
            .where(
                BookModel.is_active.is_(True),
                BookModel.author.has(
                    AuthorModel.is_active.is_(True)
                ),
            )
        )

        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def update(
            self,
            book: BookModel,
    ):
        await self.db.commit()

        await self.db.refresh(book)

        return book

    async def soft_delete(
            self,
            book: BookModel,
    ):
        book.is_active = False

        await self.db.commit()
